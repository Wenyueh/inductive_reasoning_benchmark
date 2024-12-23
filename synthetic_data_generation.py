import argparse
import random
import time
import config
from utils import generate_all_k_strings, translate_input_output_pairs

# ISL function: input-strictly-local-k function
# rule 1: input abb --> output aba: b is changed to an a if the previous two characters are ab
# rule 2: input aaa --> aab
# rule 3: input bbb --> bba
# input: abbbb --> abaaa
# input: abbabb --> abaaba
# input-stictly-local-k function: the output of a character in a string is determined by the last k characters of the string that comes before it
# if we have an ISL-3 function: contain rules like aaa --> aab, ab --> ac, bbb --> bba


# generating rules
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
    while len(all_k_strings) < args.number_of_rules:
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

# generating rules
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
    while len(rules) < args.number_of_rules:
        new_rule = one_batch_generating_rules(args, 1)[0]
        possible_output = list(set(config.vocab).difference([new_rule[-1]])) + [''] # allow deletion
        output = random.choice(possible_output)
        if((new_rule[:-1] + output) not in rules):
            rules[new_rule] = output
    
    return rules


def generate_rules(args):
    # Check if number_of_rules is smaller than vocab_size^k
    if args.number_of_rules > args.vocab_size**args.k:
        raise ValueError('number_of_rules must be smaller than vocab_size^k')
    
    rules = []

    for i in range(args.num_of_datapoints):
        if args.type == 'ISL':
            rules.append(generate_ISL_rules(args))
        elif args.type == 'L_OSL':
            rules.append(generate_OSL_rules(args))
        elif args.type == 'R_OSL':
            rules.append(generate_OSL_rules(args))
        else:
            raise ValueError('Invalid type')
        
    return rules
    

# generate sample dataset
# S1 = {(w, w0) | [w ∈ Σ≤k ∧ f(w) = w0]}
# sample size: Sum_1^k vocab^i = vocab^1 + vocab^2 + ... + vocab^k
def generate_characteristic_sample(args, rules):
    sample = {}
    for k in range(1, args.k+1):
        one_sample_inputs = generate_all_k_strings(config.vocab, k)
        for input in one_sample_inputs:
            output = apply_rule(args, rules, input)
            sample[input] = output
    return sample

# generate size n dataset containing the sample dataset
def generate_fixed_size_dataset(args, rules, n):
    sample_dataset = generate_characteristic_sample(args, rules)
    assert n >= len(sample_dataset)
    print(n, len(sample_dataset))
    extra_datapoints_number = n - len(sample_dataset)
    n= 0
    while n < extra_datapoints_number:
        length = random.randint(1, 3*args.k)
        datapoint = ''.join([random.choice(config.vocab) for _ in range(length)])
        if datapoint not in rules:
            input = datapoint
            output = apply_rule(args, rules, input)
            sample_dataset[input] = output
            n += 1
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
    parser.add_argument('--type', type=str, default='ISL', help='ISL, L_OSL, or R_OSL')
    parser.add_argument('--k', type=int, default=2, help='number of k in ISL_k or OSL_k')
    parser.add_argument('--vocab_size', type=int, default=2, help='number of vocab')
    parser.add_argument('--number_of_rules', type=int, default=2, help='number of rules, must be smaller than vocab_size^k')
    parser.add_argument('--sample_size_times', type=int, default=10, help='number of sample to compute induction on')
    return parser

def generate_data(args, rules):
    datapoints = []
    for i in range(args.num_of_datapoints):
        # Generate rules
        rules_i = rules[i]
        # Generate sample dataset
        sample_dataset = generate_characteristic_sample(args, rules_i)
        sample_dataset = generate_fixed_size_dataset(args, rules_i, args.sample_size_times*len(sample_dataset))

        prompt = translate_input_output_pairs(args, sample_dataset)
        datapoints.append([sample_dataset, prompt])

    return datapoints

if __name__ == '__main__':
    parser = synthetic_data_parser()
    args = parser.parse_args()

    # Check if number_of_rules is smaller than vocab_size^k
    if args.number_of_rules > args.vocab_size**args.k:
        raise ValueError('number_of_rules must be smaller than vocab_size^k')

    # Generate vocab
    config.vocab = list('abcdefghijklmnopqrstuvwxyz'[:args.vocab_size])

    # Generate rules
    rules = generate_rules(args)
    print(rules)
    print("=====================================")


    # Generate sample dataset
    sample_dataset = generate_characteristic_sample(args, rules)
    sample_dataset = generate_fixed_size_dataset(args, rules, 2*len(sample_dataset))

    prompt = translate_input_output_pairs(args, sample_dataset)
    print(prompt)

