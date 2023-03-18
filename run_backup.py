import hydra
from omegaconf import DictConfig, OmegaConf

from src.increment_backup import IncrementBackup

@hydra.main(version_base=None, config_path="conf", config_name="config")
def run_backup(cfg : DictConfig) -> None:
    backup_runner = IncrementBackup(cfg)
    backup_runner.run()

if __name__ == "__main__":
    run_backup()
