import argparse, os, random, config, json, sys, time
from tqdm import tqdm
from synthetic_data_generation import synthetic_data_parser, generate_rules, generate_data, apply_rule

sys.path.add('..')
from model import call_model
from utils import extract_answer


def evaluation_single_datapoint(args, data, ground_truth_rules, predicted_rules):
    # for i,o in ground_truth_rules.items():
    #     ground_truth_rules[i] = i[:args.k-1] + ground_truth_rules[i]
    def evaluate_precision_recall(ground_truth_rules, predicted_rules):
        recall = 0
        precision = 0

        correct = 0
        for key in ground_truth_rules:
            if key in predicted_rules and ground_truth_rules[key] == predicted_rules[key]:
                correct += 1

        recall = correct/len(ground_truth_rules)
        precision = correct/len(predicted_rules)
        return recall, precision
    
    def evaluate_compatibility(data, predicted_rules):
        # for i,o in predicted_rules.items():
        #     predicted_rules[i] = predicted_rules[i][args.k-1:]
        for input, output in data.items():
            if apply_rule(args, predicted_rules, input.strip()) != output:
                return False
        return True
    
    if args.type == 'R_OSL':
        reverse_predicted_rules = {}
        for k,v in predicted_rules.items():
            reverse_predicted_rules[k[::-1]] = v
        predicted_rules = reverse_predicted_rules
    recall, precision = evaluate_precision_recall(ground_truth_rules, predicted_rules)
    compatibility = evaluate_compatibility(data, predicted_rules)

    return recall, precision, compatibility

def run_inference_and_evaluation(args, datapoints, rules):
    tosave = []
    average_recall = []
    average_precision = []
    average_compatibility = []
    for i, datapoint in enumerate(tqdm(datapoints)):
        one_data_to_save = {}
        output = call_model(args, datapoint[1])
        answer = extract_answer(output)
        recall, precision, compatibility = evaluation_single_datapoint(args, datapoint[0], rules[i], answer)
        print(f'Recall: {recall}, Precision: {precision}, Compatibility: {compatibility}')
        average_recall.append(recall)
        average_precision.append(precision)
        average_compatibility.append(compatibility)
        one_data_to_save['sample_data'] = datapoint[0]
        one_data_to_save['input_prompt'] = datapoint[1]
        one_data_to_save['ground_truth_rules'] = rules[i]
        one_data_to_save['output'] = output
        one_data_to_save['predicted_rules'] = answer
        one_data_to_save['recall'] = recall
        one_data_to_save['precision'] = precision
        one_data_to_save['compatibility'] = compatibility

        tosave.append(one_data_to_save)

    average_recall = sum(average_recall)/len(average_recall)
    average_precision = sum(average_precision)/len(average_precision)
    average_compatibility = sum(average_compatibility)/len(average_compatibility)

    print('Print Current Congifuration:')
    print(f'function type: {args.type}, k: {args.k}, vocab_size: {args.vocab_size}, number_of_rules: {args.number_of_rules}')
    print(f'Average Recall: {average_recall}')
    print(f'Average Precision: {average_precision}')
    print(f'Average Compatibility: {average_compatibility}')

    tosave = {'original_data': tosave, 'average_recall': average_recall, 'average_precision': average_precision, 'average_compatibility': average_compatibility, 'k': args.k, 'vocab_size': args.vocab_size, 'number_of_rules': args.number_of_rules, 'type': args.type}

    with open(args.save_directory, 'a') as f:
        json.dump(tosave, f)

    return average_recall, average_precision, average_compatibility

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parameters for experiment setting
    parser.add_argument('--model', type=str, default="Qwen/QwQ-32B-Preview")
    parser.add_argument('--num_of_datapoints', type=int, default=10)

    # parameters for synthetic data generation
    parser.add_argument('--k', type=int, default=4, help='number of k in ISL_k or OSL_k')
    parser.add_argument('--vocab_size', type=int, default=8, help='number of vocab')
    parser.add_argument('--number_of_rules', type=int, default=4, help='number of rules, must be smaller than vocab_size^k')
    parser.add_argument('--sample_size_times', type=int, default=2, help='number of sample to compute induction on, 1 means it is just the characteristic sample')
    parser.add_argument('--reevaluate', action='store_true', help='re-evaluate the result')

    parser.add_argument('--repeat', action='store_true', help='repeat the sample set')
    args = parser.parse_args()

    model_name = args.model.replace('/', '_')

    save_directory = f'standard_benchmark_result/{model_name}.json'

    with open(save_directory, mode='w') as f:
        json.dump([], f)
    
    random.seed(0)

    # Generate vocab
    config.vocab = list('abcdefghijklmnopqrstuvwxyz'[:args.vocab_size])

    recall = 0
    precision = 0
    compatibility = 0
    for type in ['ISL', 'L_OSL', 'R_OSL']:
        args.type = type
        total_weight = 0
        scores = []
        for k in range(2, args.k+1): # k = 2, 3, 4
            for vocab_size in range(5, args.vocab_size+1): # vocab_size = 5, 6, 7, 8
                for number_of_rules in range(3, args.number_of_rules+1): # number_of_rules = 3, 4, 5
                    number_of_rules = min(number_of_rules, vocab_size**k)
                    args.k = k
                    args.vocab_size = vocab_size
                    args.number_of_rules = number_of_rules

                    weight = vocab_size**k * number_of_rules

                    rules = generate_rules(args)
                    datapoints = generate_data(args, rules)

                    average_recall, average_precision, average_compatibility = run_inference_and_evaluation(args, datapoints, rules)
                    scores.append((average_recall, average_precision, average_compatibility, weight))

                    total_weight += weight

        weighted_scores = [[score[0], score[1], score[2], score[3]/total_weight] for score in scores]

        weighted_recall = sum([score[0]*score[3] for score in weighted_scores])
        weighted_precision = sum([score[1]*score[3] for score in weighted_scores])
        weighted_compatibility = sum([score[2]*score[3] for score in weighted_scores])

        print(f"FINISHING {type} FUNCTIONS!")
        print(f'Weighted {type} Recall: {weighted_recall}')
        print(f'Weighted {type} Precision: {weighted_precision}')
        print(f'Weighted {type} Compatibility: {weighted_compatibility}')
        with open(save_directory, 'a') as f:
            json.dump({f'{type}_average_recall': recall, f'{type}_average_precision': precision, f'{type}_average_compatibility': compatibility}, f)

        recall += weighted_recall
        precision += weighted_precision
        compatibility += weighted_compatibility

    print(f'Average Recall: {recall}')
    print(f'Average Precision: {precision}')
    print(f'Average Compatibility: {compatibility}')

    with open(save_directory, 'a') as f:
        json.dump({'average_recall': recall, 'average_precision': precision, 'average_compatibility': compatibility}, f)
