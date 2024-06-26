from src.data import DataModule
from src.model import ModelModule
from src.experiment import ExperimentModule
from src.analysis import AnalysisModule
import torch
from vllm import SamplingParams
import yaml
from config import args
import numpy as np
import random
import logging
import os

# Load configuration from YAML
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Fix the random seed for reproducibility of experiments.
def fix_randomness(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)

def initialize_logger(log_file='./log/experiment.log'):
    
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('experiment_logger')
    logger.setLevel(logging.DEBUG)
    
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_file)
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)
    
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger

def main(args, config, prompts):
    logger = initialize_logger()
    logger.info(f"Using configuration: {config}")

    # Fix the random seed
    fix_randomness(args.seed)

    # Module Initialization
    model_module = ModelModule(config['model_ckpt'], gpu_args=args.num_gpus, use_vllm = args.use_vllm, model_branch=args.model_branch)

    # Sampling parameters
    sampling_params = config['sampling_params']
    sampling_params['seed'] = args.seed
    sampling_params = SamplingParams(**sampling_params)

    # Experiment
    for nation, prompt_group in prompts.items():
        for prompt in prompt_group:
            data_module = DataModule(config['dataset_name'], args.dataset_subset)
            experiment_module = ExperimentModule(data_module, model_module, logger)
            results = experiment_module.run_experiment(prompt, sampling_params, args.exp_settings)
            analysis_module = AnalysisModule(config, nation, prompt, results)
            report = analysis_module.generate_report(args.exp_report_file)
            print(f"Results for prompt: '{prompt}'")
            print(report)
            print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    args_cli = args.get_args()
    config = load_config(args_cli.config_file)
    prompts = load_config(args_cli.prompts_file)
    print(config)
    print(args_cli)
    print(prompts)
    main(args_cli, config, prompts)
