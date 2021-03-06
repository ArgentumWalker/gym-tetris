import numpy as np
import gym
from gym import spaces
import gym_tetris.tetris_engine as game


class TetrisEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self):
        # open up a game state to communicate with emulator
        self.game_state = game.GameState()
        self._action_set = self.game_state.getActionSet()
        self.action_space = spaces.Discrete(len(self._action_set))
        self.observation_space = spaces.Box(low=0, high=2, shape=(game.BOARDWIDTH, game.BOARDHEIGHT), dtype=np.int)
        self.viewer = None

    def seed(self, seed=None):
        self.game_state.seed(seed)

    def step(self, a):
        self._action_set = np.zeros([len(self._action_set)])
        self._action_set[a] = 1
        reward = 0.0
        state, reward, terminal = self.game_state.frame_step(self._action_set)
        return state, reward, terminal, {}

    def _get_image(self):
        return self.game_state.getImage()

    @property
    def _n_actions(self):
        return len(self._action_set)

    # return: (states, observations)
    def reset(self):
        self.game_state.reinit()
        return self.game_state.get_observation()

    def render(self, mode='human', close=False):
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return
        img = self._get_image()
        if mode == 'rgb_array':
            return img
        elif mode == 'human':
            from gym.envs.classic_control import rendering
            if self.viewer is None:
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(img)

