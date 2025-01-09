import random

# generating all length k string from vocab
def generate_all_k_strings(vocab, k):
    if k == 0:
        return ['']
    if k == 1:
        return vocab
    all_k_strings = []
    for k_string in generate_all_k_strings(vocab, k-1):
        for char in vocab:
            all_k_strings.append(k_string + char)
    return all_k_strings

ISL_prompt = """
Think step by step before providing the rules.

Provide a minimum set of rules that describe the input-output transformations, i.e. how an input character is transformed into its corresponding output character based on input characters coming before it in the input.
Each rule describes how a character in the input is transformed into the output based on the context of the input characters preceding it.

For example: 
a rule 'abc --> a' means that the input character 'c' is transformed into 'a' in the output when it is preceded by 'ab' in the input. 
Another example:
a rule 'fqerrqb --> s' means that the input character 'b' is transformed into 's' in the output when it is preceded by 'fqerrq' in the input.
Therefore the left part of the rule basically describe the input context in which the input character is transformed into the output character.
Notice that the last character of the left part is the character to be transformed. 
The right part of the rule is the output character that the input character is transformed into. It can be a single character or a sequence of characters, it can also be empty string.

You don't need to provide trivial rules where input and output are the same, like 'abdsa -> a' or 'frqeb -> b'.
Notice that the left part of each rule always have length <= {}. 

Write rules in the following format:
left -> right

Surround rules by XML tags <START> and <END> like below:

<START>
left1 -> right1
left2 -> right2
...
leftn -> rightn
<END>

THE RIGHT PART OF THE RULE SHOULD ONLY CONTAIN WHAT THE LAST CHARACTER OF THE LEFT PART IS TRANSFORMED INTO INSTEAD OF THE WHOLE STRING.
THINK STEP BY STEP BEFORE PROVIDING THE RULES.
"""

L_OSL_prompt = """
Think step by step before providing the rules.

Provide a minimum set of rules that describe the input-output transformations, i.e. how an input character is transformed into its corresponding output character based on output characters preceding it in the output.
Each rule describes how a character in the input is transformed into the output based on the context of the input characters preceding it.

For example:
a rule 'abc --> a' means that the input character 'c' is transformed into 'a' when 'c' is preceded by 'ab' in the output.
Another example:
a rule 'fqerrqb --> s' means that the input character 'b' is transformed into 's' when 'b' is preceded by 'fqerrq' in the output.
Therefore the left part of the rule basically describe the output context in which the input character is transformed into the output character.
Notice that the last character of the left part is the character to be transformed. 
The right part of the rule is the output character that the input character is transformed into. It can be a single character or a sequence of characters, it can also be empty string.

You don't need to provide trivial rules where no change is made, like 'ab -> b'.
Notice that the left part of each rule always have length <= {}. 

Write rules in the following format:
left -> right

Surround rules by XML tags <START> and <END> like below:

<START>
left1 -> right1
left2 -> right2
...
leftn -> rightn
<END>

THE RIGHT PART OF THE RULE SHOULD ONLY CONTAIN WHAT THE LAST CHARACTER OF THE LEFT PART IS TRANSFORMED INTO INSTEAD OF THE WHOLE STRING.
THINK STEP BY STEP BEFORE PROVIDING THE RULES.
"""

R_OSL_prompt = """
Think step by step before providing the rules.

Provide a minimum set of rules that describe the input-output transformations, i.e. how an input character is transformed into its corresponding output character based on output characters preceding it in the output.
Each rule describes how a character in the input is transformed into the output based on the context of the input characters succeeding it.

For example:
a rule 'abc --> b' means that the input character 'a' is transformed into 'b' when 'a' is succeeded by 'bc' in the output.
Another example:
a rule 'fqerrqb --> s' means that the input character 'f' is transformed into 's' when 'f' is succeeded by 'qerrqb' in the output.
Therefore the left part of the rule basically describe the output context in which the input character is transformed into the output character.
Notice that the first character of the left part is the character to be transformed. 
The right part of the rule is the output character that the input character is transformed into. It can be a single character or a sequence of characters, it can also be empty string.

You don't need to provide trivial rules where no change is made, like 'ab -> a'.
Notice that the left part of each rule always have length <= {}. 

Write rules in the following format:
left -> right

Surround rules by XML tags <START> and <END> like below:

<START>
left1 -> right1
left2 -> right2
...
leftn -> rightn
<END>

THE RIGHT PART OF THE RULE SHOULD ONLY CONTAIN WHAT THE LAST CHARACTER OF THE LEFT PART IS TRANSFORMED INTO INSTEAD OF THE WHOLE STRING.
THINK STEP BY STEP BEFORE PROVIDING THE RULES.
"""

def translate_input_output_pairs(args, input_output_pairs):
    input_output_pairs_keys = list(input_output_pairs.keys())
    random.shuffle(input_output_pairs_keys)
    input_output_pairs = {key: input_output_pairs[key] for key in input_output_pairs_keys}
    k = args.k
    prompt = """
Below is a list of input-output pairs. Please provide a set of rules that can generate the output from the input.

"""
    for input, output in input_output_pairs.items():
        prompt += f"{input} -> {output}\n"

    if args.type == 'ISL':
        prompt += ISL_prompt.format(k)
    elif args.type == 'L_OSL':
        prompt += L_OSL_prompt.format(k)
    elif args.type == 'R_OSL':
        prompt += R_OSL_prompt.format(k)

    return prompt

def extract_markdown_answer(output):
    starts = [i for i in range(len(output)) if output.startswith('<START>', i)]
    ends = [i for i in range(len(output)) if output.startswith('<END>', i)]
    last_start = starts[-1]
    last_end = ends[-1]
    output = output[last_start:last_end]

    rules = {}
    lines = output.split('\n')
    for line in lines:
        if '->' in line:
            rule = line.split('->')

            # remove initial white spaces
            if(rule[0][-1] == ' '):
                rule[0] = rule[0][:-1] 
            if(rule[1][0] == ' '):
                rule[1] = rule[1][1:]

            input = ""
            outpt = ""
            # find alphabetical portion of input and output
            for i in range(len(rule[0]) - 1, -1, -1):
                if rule[0][i].isalpha():  
                    input = rule[0][i] + input
                else:
                    break
            for i in range(len(rule[1])):
                if(rule[1][i].isalpha()):
                    outpt = outpt + rule[1][i]
                else:
                    break
            
            rules[input] = outpt
            
    return rules

def extract_string_answer(output):
    starts = [i for i in range(len(output)) if output.startswith('<START>', i)]
    ends = [i for i in range(len(output)) if output.startswith('<END>', i)]
    if len(starts) == 0 or len(ends) == 0:
        return {'':''}
    if len(starts) == len(ends):
        last_start = starts[-1]
        last_end = ends[-1]
    else:
        early = min(len(starts), len(ends))
        last_start = starts[early-1]
        last_end = ends[early-1]

    output = output[last_start:last_end].replace('\n\n', '\n')

    rules = {}
    lines = output.split('\n')
    for line in lines:
        if '->' in line:
            rule = line.split('->')
            rules[rule[0].strip()] = rule[1].strip()

    if rules == {}:
        return {'':''}
    
    return rules

def extract_answer(output):
    if 'text{<START>}' in output:
        rules = extract_markdown_answer(output)
    else:
        rules = extract_string_answer(output)

    return rules



if __name__ == '__main__':
    k = 1
    print(ISL_prompt.format(k))
    # vocab = ['a', 'b']
    # k = 3
    # print(generate_all_k_strings(vocab, k)) # ['aaa', 'aab', 'aba', 'abb', 'baa', 'bab', 'bba', 'bbb']
