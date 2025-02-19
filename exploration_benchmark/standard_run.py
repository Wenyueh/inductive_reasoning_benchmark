import argparse, os, random, config, json, sys, time
from tqdm import tqdm
from exploration_data_generation import generate_data, generate_rules, apply_rule, extract_answer
from model import call_model


def evaluation_single_datapoint(args, data, ground_truth_rules, predicted_rules):
    def evaluate_compatibility(data, predicted_rules):
        # for i,o in predicted_rules.items():
        #     predicted_rules[i] = predicted_rules[i][args.k-1:]
        for input, output in data.items():
            if apply_rule(args, predicted_rules, input.strip()) != output:
                return False
        return True
    
    def minimum_description_or_not(ground_truth_rules, predicted_rules):
        length_of_ground_truth = sum([len(k) for k in ground_truth_rules.keys()])
        length_of_predicted = sum([len(k) for k in predicted_rules.keys()])
        if length_of_predicted <= length_of_ground_truth:
            return True
        return False

    is_minimum_description = None
    compatibility = evaluate_compatibility(data, predicted_rules)

    if compatibility:
        is_minimum_description = minimum_description_or_not(ground_truth_rules, predicted_rules)

    return compatibility, is_minimum_description

def run_inference_and_evaluation(args, datapoints, rules, existent_save_directory):
    tosave = []
    average_compatibility = []
    average_length = []
    for i, datapoint in enumerate(tqdm(datapoints)):
        one_data_to_save = {}
        output = call_model(args, datapoint[1])
        answer = extract_answer(output)
        compatibility, is_minimum_description = evaluation_single_datapoint(args, datapoint[0], rules[i], answer)
        average_compatibility.append(compatibility)
        if is_minimum_description is not None:
            average_length.append(is_minimum_description)
        one_data_to_save['sample_data'] = datapoint[0]
        one_data_to_save['input_prompt'] = datapoint[1]
        one_data_to_save['ground_truth_rules'] = rules[i]
        one_data_to_save['output'] = output
        one_data_to_save['predicted_rules'] = answer
        one_data_to_save['is_minimum_description'] = is_minimum_description
        one_data_to_save['compatibility'] = compatibility

        tosave.append(one_data_to_save)

    average_is_minimum_description = 0
    if len(average_length) > 0:
        average_is_minimum_description = sum(average_length)/len(average_length)
    average_compatibility = sum(average_compatibility)/len(average_compatibility)

    print('Print Current Configuration:')
    print(f'function type: IOSL, k: {args.k}, vocab_size: {args.vocab_size}, number_of_rules: {args.number_of_rules}')
    print(f'Average is_minimum_description: {average_is_minimum_description}')
    print(f'Average Compatibility: {average_compatibility}')

    tosave = {'original_data': tosave, 'average_is_minimum_description': average_is_minimum_description, 'average_compatibility': average_compatibility, 'k': args.k, 'vocab_size': args.vocab_size, 'number_of_rules': args.number_of_rules, 'type': args.type}

    with open(existent_save_directory, 'w') as f:
        json.dump(tosave, f, indent=4)

    with open(args.save_directory, 'a') as f:
        json.dump(tosave, f)

    return average_compatibility, average_is_minimum_description

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parameters for synthetic data generation
    parser.add_argument('--type', type=str, default='IOSL', help='only IOSL is supported')
    parser.add_argument('--k', type=int, default=4, help='number of k in ISL_k or OSL_k')
    parser.add_argument('--vocab_size', type=int, default=8, help='number of vocab')
    parser.add_argument('--number_of_rules', type=int, default=5, help='number of rules, must be smaller than vocab_size^k')
    parser.add_argument('--sample_size', type=int, default=100, help='number of sample to compute induction on')
    parser.add_argument('--shot_number', type=int, default=1)
    parser.add_argument('--num_of_datapoints', type=int, default=10)

    # parameters for experiment setting
    parser.add_argument('--model', type=str, default="Qwen/QwQ-32B-Preview")
    parser.add_argument('--reevaluate', action='store_true', help='re-evaluate the result')

    args = parser.parse_args()

    model_name = args.model.replace('/', '_')

    args.save_directory = f'exploration_result/{model_name}.json'
    if not os.path.exists('exploration_result'):
        os.makedirs('exploration_result')

    with open(args.save_directory, mode='w') as f:
        json.dump([], f)
    
    random.seed(0)

    # Generate vocab
    config.vocab = list('abcdefghijklmnopqrstuvwxyz'[:args.vocab_size])

    recall = 0
    precision = 0
    compatibility = 0
    total_weight = 0
    scores = []
    assert args.k > 2, 'k must be larger than 2'
    assert args.vocab_size > 5, 'vocab_size must be larger than 5'
    assert args.number_of_rules > 3, 'number_of_rules must be larger than 3'
    for k in range(2, args.k+1): # k = 2, 3, 4
        for vocab_size in range(5, args.vocab_size+1): # vocab_size = 5, 6, 7, 8
            for number_of_rules in range(3, args.number_of_rules+1): # number_of_rules = 3, 4, 5

                # save each individual setting result
                sample_size = min(args.sample_size, vocab_size**k * 2)
                model_name = args.model.replace('/', '_')
                existent_save_directory = f'result/{model_name}_{k}_{vocab_size}_{number_of_rules}_{sample_size}.json'
                if not os.path.exists('result'):
                    os.mkdir('result')

                print(f"Start running benchmarking with k={k}, vocab_size={vocab_size}, number_of_rules={number_of_rules}")
                if os.path.exists(existent_save_directory):
                    with open(existent_save_directory, 'r') as f:
                        data = json.load(f)
                    average_is_minimum_description = data['average_is_minimum_description']
                    average_compatibility = data['average_compatibility']
                else:
                    number_of_rules = min(number_of_rules, vocab_size**k)
                    args.k = k
                    args.vocab_size = vocab_size
                    args.number_of_rules = number_of_rules

                    args.sample_size = args.vocab_size**k * 2

                    weight = vocab_size**k * number_of_rules

                    rules = generate_rules(args)
                    datapoints = generate_data(args, rules)

                    average_compatibility, average_is_minimum_description = run_inference_and_evaluation(args, datapoints, rules, existent_save_directory)
                scores.append((average_compatibility, average_is_minimum_description, weight))

                total_weight += weight

    weighted_scores = [[score[0], score[1], score[2]/total_weight] for score in scores]

    weighted_compatibility = sum([score[0]*score[3] for score in weighted_scores])
    weighted_is_minimum_description = sum([score[1]*score[3] for score in weighted_scores])

    print(f"FINISHING Benchmarking!")
    print(f'Weighted IOSL Compatibility: {weighted_compatibility}')
    print(f'Weighted IOSL Is_minimum_description: {weighted_is_minimum_description}')

    with open(args.save_directory, 'a') as f:
        json.dump({f'{type}_average_recall': recall, f'{type}_average_precision': precision, f'{type}_average_compatibility': compatibility}, f)
