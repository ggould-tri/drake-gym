import wandb_pre_import_mods_for_bazel

import argparse

import gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import (
    DummyVecEnv,
    SubprocVecEnv,
    VecVideoRecorder,
)
import torch as th
import wandb
from wandb.integration.sb3 import WandbCallback

from pydrake.geometry import StartMeshcat

gym.envs.register(id="Cartpole-v0",
                  entry_point="drake_gym.examples.envs.cart_pole.cart_pole:CartpoleEnv")  # noqa

parser = argparse.ArgumentParser(
    description="Train a policy for"
    "//drake_gym/examples.envs.cart_pole:cart_pole.")
parser.add_argument('--test', action='store_true')
parser.add_argument('--train_single_env', action='store_true')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--log_path', help="path to the logs directory.")
args = parser.parse_args()

config = {
    "policy_type": "MlpPolicy",
    "total_timesteps": 1e6,
    "env_name": "Cartpole-v0",
    "num_workers": 10,
    "env_time_limit": 7,
    "local_log_dir":
        args.log_path if args.log_path is not None else "./rl/tmp/Cartpole/",
    "model_save_freq": 1e4,
    "policy_kwargs": dict(activation_fn=th.nn.ReLU,
                          net_arch=[dict(pi=[64, 64, 64], vf=[64, 64, 64])]),
    "observation_noise": True,
    "disturbances": True,
}

if __name__ == '__main__':
    env_name = config["env_name"]
    if args.test:
        num_env = 2
    elif args.train_single_env:
        num_env = 1
    else:
        num_env = config["num_workers"]
    time_limit = config["env_time_limit"] if not args.test else 0.5
    log_dir = config["local_log_dir"]
    policy_type = config["policy_type"]
    total_timesteps = config["total_timesteps"] if not args.test else 5
    policy_kwargs = config["policy_kwargs"] if not args.test else None
    eval_freq = config["model_save_freq"]
    obs_noise = config["observation_noise"]
    add_disturbances = config["disturbances"]

    if args.test:
        run = wandb.init(mode="disabled")
    else:
        run = wandb.init(
            project="sb3_test",
            config=config,
            sync_tensorboard=True,  # Auto-upload sb3's tensorboard metrics.
            monitor_gym=True,  # Auto-upload the videos of agents playing.
            save_code=True,
        )

    if not args.train_single_env:
        env = make_vec_env(env_name,
                           n_envs=num_env,
                           seed=0,
                           vec_env_cls=SubprocVecEnv,
                           env_kwargs={
                               'time_limit': time_limit,
                               'obs_noise': obs_noise,
                               'add_disturbances': add_disturbances,
                           })
    else:
        meshcat = StartMeshcat()
        env = gym.make(env_name,
                       meshcat=meshcat,
                       time_limit=time_limit,
                       debug=args.debug,
                       obs_noise=obs_noise,
                       )
        check_env(env)
        input("Open meshcat (optional). Press Enter to continue...")

    if args.test:
        model = PPO(policy_type, env, n_steps=4, n_epochs=2,
                    batch_size=8, policy_kwargs=policy_kwargs)
    else:
        model = PPO(policy_type, env, n_steps=int(2048/num_env), n_epochs=10,
                    # In SB3, this is the mini-batch size.
                    # https://github.com/DLR-RM/stable-baselines3/blob/master/docs/modules/ppo.rst
                    batch_size=64*num_env,
                    verbose=1, tensorboard_log=log_dir +
                    f"runs/{run.id}", policy_kwargs=policy_kwargs)

    # Separate evaluation env.
    eval_env = gym.make(env_name,
                        time_limit=time_limit,
                        obs_noise=obs_noise,
                        monitoring_camera=True,
                        )
    eval_env = DummyVecEnv([lambda: eval_env])
    # Record a video every 1 evaluation rollouts.
    eval_env = VecVideoRecorder(
                        eval_env,
                        log_dir+f"videos/{run.id}",
                        record_video_trigger=lambda x: x % 1 == 0,
                        video_length=200)
    # Use deterministic actions for evaluation.
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=log_dir+f'eval_logs/{run.id}',
        log_path=log_dir+f'eval_logs/{run.id}',
        eval_freq=eval_freq,
        deterministic=True,
        render=False)

    model.learn(
        total_timesteps=total_timesteps,
        callback=[WandbCallback(
            gradient_save_freq=1e3,
            model_save_path=log_dir+f"models/{run.id}",
            verbose=2,
            model_save_freq=config["model_save_freq"],
            ),
            eval_callback]
    )
    run.finish()
