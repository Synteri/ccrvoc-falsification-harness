from ccrvoc.config import load_config
from ccrvoc.experiment import run_experiment

print(run_experiment(load_config("configs/full.yaml"), "artifacts"))
