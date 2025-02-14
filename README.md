# Inductive Reasoning Benchmark

<p align="center">
  <img width="742" alt="Screen Shot 2025-02-14 at 5 05 59 PM" src="https://github.com/user-attachments/assets/b7cbc723-01cc-45b4-ac61-18822ebf05ae" />
</p>



## Abstract
Large language models (LLMs) have shown remarkable improvements in reasoning and many existing benchmarks have been addressed by models such as o1 and o3 either fully or partially. However, a majority of these benchmarks emphasize deductive reasoning, including mathematical and coding tasks in which rules such as mathematical axioms or programming syntax are clearly defined, based on which LLMs can plan and apply these rules to arrive at a solution. In contrast, \textit{inductive reasoning}, where one infers the underlying rules from observed data, remains less explored. Such inductive processes lie at the heart of scientific discovery, as they enable researchers to extract general principles from empirical observations. To assess whether LLMs possess this capacity, we introduce \textbf{InductionBench}, a new benchmark designed to evaluate the inductive reasoning ability of LLMs. Our experimental findings reveal that even the most advanced modelw available struggle to master the simplest complexity classes within the subregular hierarchy of functions, highlighting a notable deficiency in current LLMs' inductive reasoning capabilities.


## QuickStart
Install environment
```
conda create --name induction python=3.9
conda activate induction

git clone https://github.com/Wenyueh/inductive_reasoning_benchmark.git
cd inductive_reasoning_benchmark
pip install -r requirements.txt
```
Add API keys to run models through APIs, you can add open-source models in model.py
```
export OPENAI_AI_API = 'you api key'
export CLAUDE_AI_API = 'you api key'
export TOGETHER_AI_API = 'you api key'
```
Run experiment in a single setting in the provably correct benchmark
```
cd provable_benchmark
python inference.py --type ISL --model mdoel_name --k 2 --vocab_size 2 --number_of_rules 1 --sample_size_times 2
# the simplest ISL function class with smallest hypothesis space
```
To run the standard benchmark to directly obtain leaderboard result
```
cd provable_benchmark
python standard_run.py
```
