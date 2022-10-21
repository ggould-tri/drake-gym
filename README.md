Drake Gym
=========

Drake Gym is an implementation of OpenAI's "Gym" interface for reinforcement
learning which uses a Drake `Simulator` as a backend.  The Gym interface
(provided by [the python `gym` module](https://pypi.org/project/gym/) simply
models a time-stepped process with an action space, a reward function, and
some form of state observation.

In order to use a Gym, code must implement a `gym.Env` (in this case the
actual `Simulator` wrapped via `DrakeGymEnv`) and must run the Gym within an
RL engine of some sort (that's usually an algorithm chosen from
[Stable Baselines 3](https://stable-baselines3.readthedocs.io/en/master/index.html)
but could also be from `nevergrad` or some other source of gradient-free
optimizers).

Setup
-----

Most Drake consumers will want to use a virtual environment (or, equivalently,
a notebook server) to manage dependencies in their runtime.  A
`external/requirements.txt` file is provided to make this more convenient.
You can set up a virtual environment to run this code via:

    python3 -m venv $HOME/drake_gym_venv --prompt drake_gym
    . $HOME/drake_gym_venv/bin/activate
    pip install -r external/requirements.txt

Bazel automatically sets up and uses a similar virtual environment as part of
its sandboxing process, so the above IS NOT required if all you are doing is
running `bazel` commands.

Note that if you have installed `matplotlib` via `apt`, this may confuse
`bazel test` and cause surprising failures.

Examples
--------

### Box Flipup

A trivial example of training a 2-d box flipper is provided; invoke
it via:

    bazel run //drake_gym/examples:train_box_flipup

Depending on your machine, you should see the reward (`ep_rew_mean`) number
increase slowly from ~500 to ~700 in an hour or so, which means that training
is in fact making a more successful policy.

You will also occasionally see errors about "MultibodyPlant's discrete
update solver failed to converge."  These are expected as the RL explores
policy approaches that run the edge of simulatability (e.g. extremely
energetic collisions).  You should also see the frequency of these errors
first increase (as the policy learns to reliably make contact) and then
decrease (as the low rewards from breaking the sim direct the learned policy
to other approaches).

### Cart-Pole

Another example of training to stabilize a cart/pole system is provided.
It includes added noise in the observation, added random disturbances,
randomized states (position, velocity), randomized mass, a monitoring camera
for rollout logging, and integration with Wandb.

It can be invoke it via:

    bazel run //drake_gym/examples:train_cart_pole

Depending on your machine, you should see the reward increasing
from 0 to ~140 in about 20 min.

The learned model can be played with:

    bazel run //drake_gym/examples:play_cart_pole -- --model_path {path_to_zip_model_file}

A random policy can be played with:

    bazel run //drake_gym/examples:play_cart_pole -- --test

Notes
-----

 * The overall concept of Drake Gym is discussed in
   [the course notes for Russ's Robot Manipulation course](https://manipulation.csail.mit.edu/rl.html#section1)

 * The code here is borrowed from
   [the repository backing the course notebooks](https://github.com/RussTedrake/manipulation/blob/master/manipulation/drake_gym.py)
   * Where possible this code has been borrowed verbatim; small changes (e.g.
     to bazel rules, namespaces, and so forth) have been required, as have
     tests, examples, and build infrastructure.

 * Although neither Drake Gym itself nor most Envs will have excessive
   dependencies, running a Gym requires an RL engine that may quite
   heavyweight.  This package requires `stable_baselines3` (both for the
   its demonstrations and also to acceptance-test its envs), which is why it
   is not in Drake itself.
