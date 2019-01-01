from stytra import Stytra, Protocol
from stytra.stimulation.stimuli.visual import StimulusCombiner, MovingGratingStimulus, \
    HighResMovingWindmillStimulus
import pandas as pd
import numpy as np

# In this protocol, we demonstrate the use of a StimulusCombiner object to
# display simultaneously different stimuli in different regions on the screen.
class CombinedProtocol(Protocol):
    name = "combined_protocol"

    def get_stim_sequence(self):
        # Time and velocity array for two different gratings:
        t = [0, 1, 1, 6, 6, 7]
        vel = np.array([0, 0, 10, 10, 0, 0])

        # Horizontal grating (grating angle 0)
        # We define a rectangular clip mask that specifies where the stimulus
        # will be displayed ([x, y, x_len, y_len]). To see how to specify
        # arbitrary clipping masks look into clip_mask input description.
        stim_a = MovingGratingStimulus(
                df_param=pd.DataFrame(dict(t=t, vel_x=vel)),
                grating_angle=0,
                clip_mask=[0, 0, 1, 0.5])

        # Diagonal grating (grating angle 45):
        stim_b = MovingGratingStimulus(
            df_param=pd.DataFrame(dict(t=t, vel_x=vel)),
            grating_angle=45,
            clip_mask=[0, 0.5, 1, 0.5])

        # Time and theta array for the windmill:
        STEPS = 0.005
        t_wind = np.arange(0, t[-1], STEPS)
        theta = np.sin(2 * np.pi * t_wind * 0.2) * np.pi / 2

        # Windmill (a float clip mask value automatically describes a
        # circular region; see clip_mask input description):
        stim_c = HighResMovingWindmillStimulus(
            df_param=pd.DataFrame(dict(t=t_wind, theta=theta)),
            clip_mask=0.3)

        stimuli = [StimulusCombiner([stim_a, stim_b, stim_c])]
        return stimuli


if __name__ == "__main__":
    st = Stytra(protocol=CombinedProtocol())
