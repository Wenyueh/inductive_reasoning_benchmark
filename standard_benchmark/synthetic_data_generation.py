import argparse
import random, json
import time
import config
from tqdm import tqdm
import sys
from utils import generate_all_k_strings, translate_input_output_pairs, translate_fewshot_input_output_pairs

# ISL function: input-strictly-local-k function
# rule 1: input abb --> output aba: b is changed to an a if the previous two characters are ab
# rule 2: input aaa --> aab
# rule 3: input asdfbbb --> bba
# input: abbbb --> abaaa
# input: abbabb --> abaaba
# input-stictly-local-k function: the output of a character in a string is determined by the last k characters of the string that comes before it
# if we have an ISL-3 function: contain rules like aaa --> aab, ab --> ac, bbb --> bba


# generating ISL rules
def generate_ISL_rules(args):
    def one_batch_generating_rules(args, number_of_rules):
        all_k_strings = ['']*number_of_rules
        for _ in range(args.k):
            for i in range(number_of_rules):
                all_k_strings[i] += random.choice(config.vocab)

        random_k_all_k_strings = []
        for all_k_string in all_k_strings:
            length = random.randint(2, args.k)
            truncated_string = all_k_string[:length]
            is_suffix = False
            for s in random_k_all_k_strings:
                if truncated_string == s[-len(truncated_string):] or truncated_string[-len(s):] == s:
                    is_suffix = True
            if not is_suffix:
                random_k_all_k_strings.append(truncated_string)

        all_k_strings = random_k_all_k_strings
        return all_k_strings
    
    rules = {}
    all_k_strings = []
    loop_times = 0
    while len(all_k_strings) < args.number_of_rules:
        loop_times += 1
        if loop_times > 200:
            sys.exit('Cannot generate enough rules')
        number_of_rules = args.number_of_rules - len(all_k_strings)
        new_rules = one_batch_generating_rules(args, number_of_rules)
        all_k_strings += new_rules
        all_k_strings = list(set(all_k_strings))

    # if all k strings are not of length k
    # add random characters to make one of them to be of length k
    if max([len(k_string) for k_string in all_k_strings]) < args.k:
        all_k_strings[-1] = ''.join([random.choice(config.vocab) for _ in range(args.k - len(all_k_strings[-1]))]) + all_k_strings[-1] 

    for k_string in all_k_strings:
        possible_output = list(set(config.vocab).difference([k_string[-1]])) + [''] # allow deletion
        rules[k_string] = random.choice(possible_output)

    return rules

def generate_OSL_rules(args):
    # returns a list (length <= number_of_rules) of randomly generated and randomly truncated strings 
    def one_batch_generating_rules(args, number_of_rules):
        # generate number_of_rules random strings of length k from the vocab list
        all_k_strings = ['']*number_of_rules
        for _ in range(args.k):
            for i in range(number_of_rules):
                all_k_strings[i] += random.choice(config.vocab)

        # truncating generated strings to random length between 2 - k
        random_k_all_k_strings = []
        for all_k_string in all_k_strings:
            length = random.randint(2, args.k)
            truncated_string = all_k_string[:length]
            is_suffix = False
            for s in random_k_all_k_strings:
                if truncated_string == s[-len(truncated_string):] or truncated_string[-len(s):] == s:
                    is_suffix = True
            if not is_suffix:
                random_k_all_k_strings.append(truncated_string)

        all_k_strings = random_k_all_k_strings
        return all_k_strings
    
    rules = {}

    # generate first rule
    new_rule = one_batch_generating_rules(args, 1)[0]
    possible_output = list(set(config.vocab).difference([new_rule[-1]])) + [''] # allow deletion
    output = random.choice(possible_output)

    # guarantee that at least one rule will be of length k
    if len(new_rule) < args.k:
        new_rule = ''.join([random.choice(config.vocab) for _ in range(args.k - len(new_rule))]) + new_rule

    rules[new_rule] = output

    # run one_batch_generating_rules and add to rules until len(rules) = args.number_of_rules
    loop_times = 0
    while len(rules) < args.number_of_rules:
        loop_times += 1
        if loop_times > 200:
            sys.exit('Cannot generate enough rules')
        new_rule = one_batch_generating_rules(args, 1)[0]

        # checking that input is not a suffix of another input
        is_suffix = False
        for rule in rules:
            if new_rule == rule[-len(new_rule):] or new_rule[-len(rule):] == rule:
                is_suffix = True
        if is_suffix:
            continue

        possible_output = list(set(config.vocab).difference([new_rule[-1]])) + [''] # allow deletion
        output = random.choice(possible_output)

        # without suffix check
        rules[new_rule] = output

    return rules

def generate_rules(args):
    # Check if number_of_rules is smaller than vocab_size^k
    if args.number_of_rules > args.vocab_size**args.k:
        raise ValueError('number_of_rules must be smaller than vocab_size^k')
    
    rules = []

    if not args.repeat:
        for i in range(args.num_of_datapoints):
            if args.type == 'ISL':
                rules.append(generate_ISL_rules(args))
            elif args.type == 'L_OSL':
                rules.append(generate_OSL_rules(args))
            elif args.type == 'R_OSL':
                rules.append(generate_OSL_rules(args))
            else:
                raise ValueError('Invalid type')
    else:
        assert args.repeat
        model_name = args.model.replace('/', '_')
        file_name = f'{model_name}_{args.type}_{args.k}_{args.vocab_size}_{args.number_of_rules}_{args.sample_size_times}.json'
        with open('result/samplesize/'+file_name, 'r') as f:
            data = json.load(f)
            f.close()
        for i in range(args.num_of_datapoints):
            new_rules = {}
            need_modify = False
            for k,v in data['original_data'][i]['ground_truth_rules'].items():
                if len(v) > 1:
                    need_modify = True
                if v != '':
                    if v[-1] == k[-1]:
                        need_modify = True
            if need_modify:
                for k,v in data['original_data'][i]['ground_truth_rules'].items():
                    new_rules[k] = v[args.k-1:]
            else:
                new_rules = data['original_data'][i]['ground_truth_rules']
            rules.append(new_rules)
            
    return rules
    

# generate characteristic sample dataset
# S1 = {(w, w0) | [w ∈ Σ≤k ∧ f(w) = w0]}
# sample size: Sum_1^k vocab^i = vocab^1 + vocab^2 + ... + vocab^k
def generate_ISL_characteristic_sample(args, rules):
    sample = {}
    for k in range(1, args.k+1):
        one_sample_inputs = generate_all_k_strings(config.vocab, k)
        for input in one_sample_inputs:
            output = apply_rule(args, rules, input)
            sample[input] = output
    return sample

def generate_OSL_characteristic_sample(args, rules):
    def condition_satisfied(sample):
        all_possible_suffix = []
        for k in range(1, args.k+1):
            one_sample_inputs = generate_all_k_strings(config.vocab, k)
            all_possible_suffix += one_sample_inputs

        all_suffix = list(set(list(sample.values())))
        if set(all_suffix) == set(all_possible_suffix):
            return True
        else:
            return False

    def retain_shorted_input(sample):
        reversed_sample_list = [(v, k) for k, v in sample.items()]
        reversed_sample = {}
        for output, input in reversed_sample_list:
            if output not in reversed_sample:
                reversed_sample[output] = input
            # retain the shortest input
            elif len(input) < len(reversed_sample[output]):
                reversed_sample[output] = input
        sample = {v: k for k, v in reversed_sample.items()}
        return sample
        

    sample = {}
    i = 1

    # starting point of the sample from 1 to k
    for k in range((i-1)*args.k + 1, i * args.k+1):
        one_sample_inputs = generate_all_k_strings(config.vocab, k)
        for input in one_sample_inputs:
            output = apply_rule(args, rules, input)
            sample[input] = output
    sample = retain_shorted_input(sample)

    trial_number = 1
    # make sure that it includes all possible k-1 suffix
    nothing_added = True
    # if it does not include all possible suffix, keep adding until we can't add anymore
    while not condition_satisfied(sample) or trial_number < args.k:
        k = args.k + trial_number
        one_sample_inputs = list(set(generate_all_k_strings(config.vocab, k)).difference(set(generate_all_k_strings(config.vocab, k-1))))
        for input in one_sample_inputs:
            output = apply_rule(args, rules, input)
            # if same output, do not add as we don't need repetitive output suffix
            # if output > k, do not add as it is then not the minimum characterisitc sample
            if output not in sample.values() and len(output) <= args.k:
                sample[input] = output
                nothing_added = False
            elif output in sample.values() and len(input) < len([k for k, v in sample.items() if v == output][0]):
                sample[input] = output
                nothing_added = False
        sample = retain_shorted_input(sample)

        if nothing_added:
            break

        trial_number += 1

    # ensuring onwardness
    def add_intermediate_steps(args, sample):
        def find_continuation(input, sample):
            all_possible_continuation = []
            for possible_continuation, _ in sample.items():
                if possible_continuation[:len(input)] == input and len(possible_continuation) > len(input):
                    all_possible_continuation.append(possible_continuation)
            return all_possible_continuation
        def find_missing_continuation(input, all_possible_continuation):
            next_characters = set([one_continuation[len(input)] for one_continuation in all_possible_continuation])
            if next_characters == set(list(config.vocab)):
                return []
            else:
                return list(set(list(config.vocab)).difference(next_characters))
            
        # sort sample by the length of k
        sample = {k: v for k, v in sorted(sample.items(), key=lambda item: len(item[0]))}
        # find all keys in sample 'a' such that there exists 'a_1' such that 'a' is a proper prefix of 'a_1'
        new_sample = {}
        for input, output in sample.items():
            all_possible_continuation = find_continuation(input, sample)
            if all_possible_continuation:
                missing_continuation = find_missing_continuation(input, all_possible_continuation)
                for m in missing_continuation:
                    new_sample[input+m] = apply_rule(args, rules, input+m)
        sample.update(new_sample)
        return sample

    sample = add_intermediate_steps(args, sample)

    return sample

def generate_characteristic_sample(args, rules):
    if args.type == 'ISL':
        return generate_ISL_characteristic_sample(args, rules)
    elif 'OSL' in args.type:
        return generate_OSL_characteristic_sample(args, rules)
    else:
        raise ValueError('Invalid type')

# generate size = n * |characteristic sample| dataset containing the sample dataset
def generate_fixed_size_dataset(args, rules, n):
    sample_dataset = generate_characteristic_sample(args, rules)

    assert n >= len(sample_dataset)
    extra_datapoints_number = n - len(sample_dataset)
    n= 0
    if not args.repeat:
        while n < extra_datapoints_number:
            length = random.randint(1, 3*args.k)
            datapoint = ''.join([random.choice(config.vocab) for _ in range(length)])
            if datapoint not in rules:
                input = datapoint
                output = apply_rule(args, rules, input)
                sample_dataset[input] = output
                n += 1
    else:
        new_dictionary = {}
        for input, output in sample_dataset.items():
            new_dictionary[input] = output
            new_input = input 
            while new_input in new_dictionary:
                new_input += ' '
            new_dictionary[new_input] = output
            n += 1
            if n >= extra_datapoints_number:
                break
        sample_dataset = new_dictionary
    return sample_dataset

# rule application
def apply_ISL_rule(args, rules, input):
    output = ''
    for i in range(len(input)):
        # go through all k
        modified = False
        for k in range(1, args.k+1):
            suffix = input[:i+1][-k:]     
            if suffix in rules:
                output += rules[suffix]
                modified = True
                break
        if not modified:
            output += input[i]
    return output

# rule application
def apply_L_OSL_rule(args, rules, input):
    output = ''
    for i in range(len(input)):
        # go through all k
        output += input[i]
        for k in range(1, args.k+1):
            suffix = output[:i+1][-k:]     
            if suffix in rules:
                output = output[:-1]
                output += rules[suffix]
                break
    return output

# rule application
def apply_R_OSL_rule(args, rules, input):
    input = input[::-1]
    output = ''
    for i in range(len(input)):
        # go through all k
        output += input[i]
        for k in range(1, args.k+1):
            suffix = output[:i+1][-k:]     
            if suffix in rules:
                output = output[:-1]
                output += rules[suffix]
                break

    return output[::-1]


def apply_rule(args, rules, input):
    if args.type == 'ISL':
        return apply_ISL_rule(args, rules, input)
    elif args.type == 'L_OSL':
        return apply_L_OSL_rule(args, rules, input)
    elif args.type == 'R_OSL':
        return apply_R_OSL_rule(args, rules, input)
    else:
        raise ValueError('Invalid type')
    

def synthetic_data_parser():
    parser = argparse.ArgumentParser(description='Generate ISLs and OSLs')
    parser.add_argument('--type', type=str, default='L_OSL', help='ISL, L_OSL, or R_OSL')
    parser.add_argument('--k', type=int, default=2, help='number of k in ISL_k or OSL_k')
    parser.add_argument('--vocab_size', type=int, default=2, help='number of vocab')
    parser.add_argument('--number_of_rules', type=int, default=2, help='number of rules, must be smaller than vocab_size^k')
    parser.add_argument('--sample_size_times', type=int, default=10, help='number of sample to compute induction on')
    parser.add_argument('--shot_number', type=int, default=1)
    parser.add_argument('--num_of_datapoints', type=int, default=10)

    parser.add_argument('--repeat', action='store_true', help='repeat the same dataset')
    return parser

def generate_data(args, rules):
    datapoints = []
    for i in tqdm(range(args.num_of_datapoints), desc='Generating data'):
        # Generate rules
        rules_i = rules[i]
        # Generate sample dataset
        sample_dataset = generate_characteristic_sample(args, rules_i)
        sample_dataset = generate_fixed_size_dataset(args, rules_i, args.sample_size_times*len(sample_dataset))

        prompt = translate_input_output_pairs(args, sample_dataset)
        datapoints.append([sample_dataset, prompt])

    return datapoints

def generate_example(example_id, input_output_pairs, example_rule):
    input_output_pairs_keys = list(input_output_pairs.keys())
    random.shuffle(input_output_pairs_keys)
    input_output_pairs = {key: input_output_pairs[key] for key in input_output_pairs_keys}
    prompt = f"""
<example_{example_id}>
"""
    for input, output in input_output_pairs.items():
        prompt += f"(input: {input}, output: {output})\n"
    prompt += """
After some thinking, the inferred rules are:
            
<START>
{}
<END>

</example_{}>
""".format('\n'.join([f"{k} -> {v}" for k, v in example_rule.items()]), example_id)
    return prompt

def generate_few_shot_data(args, rules):
    datapoints = []
    for i in range(args.num_of_datapoints):
        # Generate rules
        rules_i = rules[i]
        # Generate sample dataset
        sample_dataset = generate_characteristic_sample(args, rules_i)
        sample_dataset = generate_fixed_size_dataset(args, rules_i, args.sample_size_times*len(sample_dataset))

        example_rule_set = []
        example_text = ''
        for example_id in range(args.shot_number):
            example_rule = rules[random.choice(list(range(len(rules))))]
            while example_rule == rules_i or example_rule in example_rule_set:
                example_rule = rules[random.choice(list(range(len(rules))))]
            example_rule_set.append(example_rule)
            sample_dataset_example = generate_characteristic_sample(args, example_rule)
            #sample_dataset_example = generate_fixed_size_dataset(args, example_rule, args.sample_size_times*len(sample_dataset_example))
            one_example = generate_example(example_id+1, sample_dataset_example, example_rule)
            example_text += one_example

        #prompt = translate_input_output_pairs(args, sample_dataset)
        prompt = translate_fewshot_input_output_pairs(args, sample_dataset, example_text)
        datapoints.append([sample_dataset, prompt])

    return datapoints

if __name__ == '__main__':
    parser = synthetic_data_parser()
    args = parser.parse_args()

    random.seed(0)

    # Check if number_of_rules is smaller than vocab_size^k
    if args.number_of_rules > args.vocab_size**args.k:
        raise ValueError('number_of_rules must be smaller than vocab_size^k')

    # Generate vocab
    config.vocab = list('abcdefghijklmnopqrstuvwxyz'[:args.vocab_size])

    # Generate rules
    rules = generate_rules(args)
    for rule in rules:
        print(rule)
        #print(rules[2])
        print("=====================================")

    sample_dataset = generate_characteristic_sample(args, rules[-1])
    sample_dataset = generate_fixed_size_dataset(args, rules[-1], args.sample_size_times*len(sample_dataset))

    for k,v in sample_dataset.items():
        print(k, v)

    # prompt = generate_few_shot_data(args, rules)
    # print(prompt[0][1])

    # input_string = 'aaabba'
    # output = apply_R_OSL_rule(args, rules[0], input_string)

    # print(output)


    # # Generate sample dataset
    # sample_dataset = generate_characteristic_sample(args, rules[0])
    # sample_dataset = generate_fixed_size_dataset(args, rules, 2*len(sample_dataset))

    # prompt = translate_input_output_pairs(args, sample_dataset)
    # print(prompt)

