import random, config, argparse

def generate_IOSL_rules(args):
    def is_suffix(rule, rules):
        for k in rules:
            if rule == k[-len(rule):] or rule[-len(k):] == k:
                return True
        return False

    rules = {}
    while len(rules) < args.number_of_rules-1:
        condition_length = random.randint(2, args.k)
        condition = ''.join([random.choice(config.vocab) for _ in range(condition_length)])
        is_input_condition = random.choice(['input', 'output'])
        if not is_suffix(condition, list(rules.keys())):
            rules[condition] = [random.choice(list(set(config.vocab).difference([condition[-1]])) + ['']), is_input_condition]

    # Add the last rule, the condition must have length k
    while len(rules) < args.number_of_rules:
        condition_length = args.k
        condition = ''.join([random.choice(config.vocab) for _ in range(condition_length)])
        is_input_condition = random.choice(['input', 'output'])
        if not is_suffix(condition, list(rules.keys())):
            rules[condition] = [random.choice(list(set(config.vocab).difference([condition[-1]])) + ['']), is_input_condition]
    return rules

def generate_rules(args):
    assert args.type == 'IOSL'
    return [generate_IOSL_rules(args) for _ in range(args.num_of_datapoints)]

def apply_IOSL_rule(args, rules, input):
    output = ''
    for i in range(len(input)):
        # go through all k
        modified = False
        for k in range(1, args.k+1):
            suffix = input[:i+1][-k:]     
            if suffix in rules and rules[suffix][1] == 'input':
                output += rules[suffix][0]
                modified = True
                break
        if not modified:
            for k in range(1, args.k+1):
                suffix = output[:i+1][-k:]     
                if suffix in rules and rules[suffix][1] == 'output':
                    output = output[:-1]
                    output += rules[suffix][0]
                    break

        if not modified:
            output += input[i]
    return output

def apply_rule(args, rules, input):
    assert args.type == 'IOSL'
    return apply_IOSL_rule(args, rules, input)


def generate_fixed_size_dataset(args, rules, n):
    assert n >= args.vocab_size**args.k, 'n must be larger than vocab_size^k'
    dataset = {}
    while len(dataset) < n:
        i = random.randint(1, 4)
        input = ''.join([random.choice(config.vocab) for _ in range(i*args.k)])
        output = apply_rule(args, rules, input)
        if input not in dataset:
            dataset[input] = output
    return dataset


def synthetic_data_parser():
    parser = argparse.ArgumentParser(description='Generate ISLs and OSLs')
    parser.add_argument('--type', type=str, default='IOSL', help='only IOSL is supported')
    parser.add_argument('--k', type=int, default=2, help='number of k in ISL_k or OSL_k')
    parser.add_argument('--vocab_size', type=int, default=2, help='number of vocab')
    parser.add_argument('--number_of_rules', type=int, default=2, help='number of rules, must be smaller than vocab_size^k')
    parser.add_argument('--sample_size', type=int, default=100, help='number of sample to compute induction on')
    parser.add_argument('--shot_number', type=int, default=1)
    parser.add_argument('--num_of_datapoints', type=int, default=10)

    parser.add_argument('--repeat', action='store_true', help='repeat the same dataset')
    return parser

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

    sample_dataset = generate_fixed_size_dataset(args, rules[-1], args.sample_size)

    for k,v in sample_dataset.items():
        print(k, v)
