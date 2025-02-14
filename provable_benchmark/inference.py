import argparse, os, random, config, json, sys, time
from tqdm import tqdm
from synthetic_data_generation import synthetic_data_parser, generate_rules, generate_data, apply_rule
from utils import extract_answer
from model import call_model


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

    print(f'Average Recall: {average_recall}')
    print(f'Average Precision: {average_precision}')
    print(f'Average Compatibility: {average_compatibility}')

    tosave = {'original_data': tosave, 'average_recall': average_recall, 'average_precision': average_precision, 'average_compatibility': average_compatibility}

    with open(args.save_directory, 'w') as f:
        json.dump(tosave, f)

def reevaluate(args, file_name):
    average_recall = []
    average_precision = []
    average_compatibility = []
    with open(file_name, 'r') as f:
        data = json.load(f)
    datapoints = data['original_data']
    for i, datapoint in enumerate(tqdm(datapoints)):
        recall, precision, compatibility = evaluation_single_datapoint(args, datapoint['sample_data'], datapoint['ground_truth_rules'], datapoint['predicted_rules'])
        average_recall.append(recall)
        average_precision.append(precision)
        average_compatibility.append(compatibility)
        datapoints[i]['recall'] = recall
        datapoints[i]['precision'] = precision
        datapoints[i]['compatibility'] = compatibility

    average_recall = sum(average_recall)/len(average_recall)
    average_precision = sum(average_precision)/len(average_precision)
    average_compatibility = sum(average_compatibility)/len(average_compatibility)

    print(data['average_recall'])
    print(data['average_precision'])
    print(data['average_compatibility'])

    print(f'Average Recall: {average_recall}')
    print(f'Average Precision: {average_precision}')
    print(f'Average Compatibility: {average_compatibility}')
    time.sleep(0.5)

    data['original_data'] = datapoints
    data['average_recall'] = average_recall
    data['average_precision'] = average_precision
    data['average_compatibility'] = average_compatibility

    with open(args.save_directory, 'w') as f:
        json.dump(data, f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parameters for experiment setting
    parser.add_argument('--model', type=str, default="Qwen/QwQ-32B-Preview")
    parser.add_argument('--num_of_datapoints', type=int, default=10)

    # parameters for synthetic data generation
    parser.add_argument('--type', type=str, default='ISL', help='ISL, L_OSL, or R_OSL')
    parser.add_argument('--k', type=int, default=2, help='number of k in ISL_k or OSL_k')
    parser.add_argument('--vocab_size', type=int, default=2, help='number of vocab')
    parser.add_argument('--number_of_rules', type=int, default=2, help='number of rules, must be smaller than vocab_size^k')
    parser.add_argument('--sample_size_times', type=int, default=4, help='number of sample to compute induction on, 1 means it is just the characteristic sample')
    parser.add_argument('--reevaluate', action='store_true', help='re-evaluate the result')

    parser.add_argument('--repeat', action='store_true', help='repeat the sample set')
    args = parser.parse_args()

    model_name = args.model.replace('/', '_')

    if args.vocab_size >= 5:
        save_directory = f'extra_table/{args.type}/{model_name}_{args.type}_{args.k}_{args.vocab_size}_{args.number_of_rules}_{args.sample_size_times}.json'
        args.save_directory = save_directory
    else:
        save_directory = f'result/{args.type}/{model_name}_{args.type}_{args.k}_{args.vocab_size}_{args.number_of_rules}_{args.sample_size_times}.json'
        args.save_directory = save_directory

    if args.repeat:
        save_directory = f'result/repeat_samplesize/{model_name}_{args.type}_{args.k}_{args.vocab_size}_{args.number_of_rules}_{args.sample_size_times}.json'
        args.save_directory = save_directory

    if os.path.exists(save_directory):
        print('This experiment has been done before: ', save_directory)
        if args.reevaluate:
            reevaluate(args, save_directory)
        sys.exit() 

    random.seed(0)

    # Generate vocab
    config.vocab = list('abcdefghijklmnopqrstuvwxyz'[:args.vocab_size])

    rules = generate_rules(args)
    datapoints = generate_data(args, rules)

    run_inference_and_evaluation(args, datapoints, rules)


