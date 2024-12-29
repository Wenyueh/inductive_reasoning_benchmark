# for k in 2 3 4
# do
#     for V in 2 3 4
#     do 
#         for R in 1 2 3
#         do 
#             for S in 1 2 3
#             do 
#                 python inference.py --type ISL --model meta-llama/Llama-3.3-70B-Instruct-Turbo --k $k --vocab_size $V --number_of_rules $R --sample_size_times $S
#             done
#         done 
#     done 
# done

for k in 2 3 4
do
    for V in 2 3 4
    do 
        for R in 1 2 3
        do 
            for S in 1 2 3
            do 
                python inference.py --type ISL --model meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo --k $k --vocab_size $V --number_of_rules $R --sample_size_times $S
            done
        done 
    done 
done


# for k in 2 3 4
# do
#     for V in 2 3 4
#     do 
#         for R in 1 2 3
#         do 
#             for S in 1 2 3
#             do 
#                 python inference.py --type ISL --model Qwen/QwQ-32B-Preview --k $k --vocab_size $V --number_of_rules $R --sample_size_times $S
#             done
#         done 
#     done 
# done


# for k in 2 3 4
# do
#     for V in 2 3 4
#     do 
#         for R in 1 2 3
#         do 
#             for S in 1 2 3
#             do 
#                 python inference.py --type ISL --model mistralai/Mixtral-8x7B-Instruct-v0.1 --k $k --vocab_size $V --number_of_rules $R --sample_size_times $S
#             done
#         done 
#     done 
# done
