from stytra import Stytra
from stytra.stimulation.stimuli import (
    FishTrackingStimulus,
    HalfFieldStimulus,
    RadialSineStimulus,
    FullFieldVisualStimulus,
    CircleStimulus,
    FishOverlayStimulus
)
from stytra.stimulation.stimuli.conditional import CenteringWrapper

from stytra.stimulation import Protocol
from lightparam import Param
from pathlib import Path


class PhototaxisProtocol(Protocol):
    name = "phototaxis"
    stytra_config = dict(
        display=dict(min_framerate=50),
        tracking=dict(method="fish", embedded=False, estimator="position"),
        camera=dict(video_file=str("/Users/Ray/Downloads/Free_swim_fish_ex.mp4"),
        min_framerate=50,),
    )

    def __init__(self):
        super().__init__()
        self.n_trials = Param(120, (0, 2400))
        self.stim_on_duration = Param(10, (0, 30))
        self.stim_off_duration = Param(10, (0, 30))
        self.center_offset = Param(0, (-100, 100))
        self.brightness = Param(255, (0, 255))

    '''def update(self):
        if self.is_tracking:
            y, x, theta = self._experiment.estimator.get_position()
            if np.isfinite(theta):
                self.x = x
                self.y = y
                self.theta = theta
        super().update()'''

    def get_stim_sequence(self):
        stimuli = []
        
        # The phototaxis stimulus for zebrafish is bright on one side of the
        # fish and dark on the other. The type function combines two classes:
        stim = type("phototaxis", (FishOverlayStimulus, FishTrackingStimulus), {})

        # The stimuli are a sequence of a phototactic stimulus and full-field
        # illumination
        for i in range(self.n_trials):

            # The stimulus of interest is wrapped in a CenteringStimulus,
            # so if the fish moves out of the field of view, a stimulus is
            # displayed which brings it back
            stimuli.append(stim(duration=self.stim_on_duration)
                
                
            )
                        #color=(self.brightness,) * 3,
                        
                        
                        
                        #center_dist=self.center_offset,
                   
                
                #CenteringWrapper(
                    #stimulus=s
            

            
           # background_color=(self.brightness,) * 3,
            #circle_color=(255, 50, 150), 
           # duration=self.stim_on_duration,
                
            stimuli.append(
                FullFieldVisualStimulus(
                    color=(self.brightness,) * 3, duration=self.stim_off_duration
                )
            )

        return stimuli


if __name__ == "__main__":
    s = Stytra(protocol=PhototaxisProtocol())
