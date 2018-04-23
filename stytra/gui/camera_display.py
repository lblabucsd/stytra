import datetime
from multiprocessing import Queue
from queue import Empty

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from pyqtgraph.parametertree import ParameterTree
from skimage.io import imsave

from stytra.tracking.diagnostics import draw_ellipse

from stytra.hardware.video import CameraControlParameters


class CameraViewWidget(QWidget):
    """ A widget to show images from the camera and display the controls.
    It does not implement a frame dispatcher so it may lag behind
    the camera at high frame rates.
    """
    def __init__(self, experiment):
        """
        :param experiment: experiment to which this belongs (Experiment class)
        """

        super().__init__()

        self.experiment = experiment
        self.camera = experiment.camera

        self.control_params = CameraControlParameters()

        # Create the layout for the camera view:
        self.camera_display_widget = pg.GraphicsLayoutWidget()

        # Display area for showing the camera image:
        self.display_area = pg.ViewBox(lockAspect=1, invertY=False)
        self.display_area.setRange(QRectF(0, 0, 640, 640), update=True,
                                   disableAutoRange=True)
        # Image to which the frame will be set, initially black:
        self.image_item = pg.ImageItem()
        self.image_item.setImage(np.zeros((640, 480), dtype=np.uint8))
        self.display_area.addItem(self.image_item)

        self.camera_display_widget.addItem(self.display_area)

        # Queue of frames coming from the camera
        if hasattr(experiment, 'frame_dispatcher'):
            self.frame_queue = self.experiment.frame_dispatcher.gui_queue
        else:
            self.frame_queue = self.camera.frame_queue
        # Queue of control parameters for the camera
        # Queue of frames coming from the camera:
        self.frame_queue = self.camera.frame_queue

        # Queue of control parameters for the camera:
        self.control_queue = self.camera.control_queue
        self.camera_rotation = self.camera.rotation
        experiment.gui_timer.timeout.connect(self.update_image)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.protocol_params_tree = ParameterTree(showHeader=False)
        self.control_params.params.sigTreeStateChanged.connect(
            self.update_controls)

        self.layout.addWidget(self.camera_display_widget)

        self.layout_control = QHBoxLayout()
        if self.control_queue is not None:
            self.params_button = QPushButton('Camera params')
            self.params_button.clicked.connect(self.show_params_gui)
            self.layout_control.addWidget(self.params_button)

        self.captureButton = QPushButton('Capture frame')
        self.captureButton.clicked.connect(self.save_image)
        self.layout_control.addWidget(self.captureButton)

        self.layout.addLayout(self.layout_control)
        self.current_image = None

        self.setLayout(self.layout)

    def update_controls(self):
        self.control_queue.put(self.control_params.get_clean_values())

    def update_image(self):
        """ Update displayed frame and empty frame source queue. This is done
        through a while loop that takes all available frames at every update.
        """

        first = True
        while True:
            try:
                # In this way, the frame displayed is actually the most
                # recent one added to the queue, as a queue is FILO:
                if first:
                    time, self.current_image = self.frame_queue.get(
                        timeout=0.001)
                    first = False
                else:
                    # Else, get to free the queue:
                    _, _ = self.frame_queue.get(timeout=0.001)

                if self.camera_rotation >= 1:
                    self.current_image = np.rot90(self.current_image,
                                                  k=self.camera_rotation)

            except Empty:
                break

        # Once obtained current image, display it:
        if self.current_image is not None:
            self.image_item.setImage(self.current_image)

    def save_image(self):
        """ Save a frame to the current directory.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        imsave(self.experiment.directory + '/' + timestamp + '_img.png',
               self.image_item.image)

    def show_params_gui(self):
        """ Parameters window for the protocol parameters.
        """
        self.protocol_params_tree.setParameters(self.control_params.params)
        self.protocol_params_tree.show()
        self.protocol_params_tree.setWindowTitle('Camera parameters')
        self.protocol_params_tree.resize(450, 600)


class CameraSelection(CameraViewWidget):
    """ Generic class for handling display of frames from a frame dispatcher
    instead of directly from the camera, and for display ROIs that can be
    used to select regions of the image and communicate their position to the
    tracking algorithm (e.g., tail starting point or eyes region).

    The changes of parameters  read through the ROI position are handled by
    via the track_params class, so they must have a corresponding entry in the
    definition of the FrameProcessingMethod of the tracking function.
    Children should define a ROI before calling parent's __init__.
    """

    def __init__(self, experiment, **kwargs):
        super().__init__(experiment, **kwargs)
        # Redefine the source of the displayed images to be the FrameProcessor
        # output queue:
        self.frame_queue = self.experiment.frame_dispatcher.gui_queue
        self.track_params = self.experiment.tracking_method.params

        # Redefine the source of the displayed images to be the FrameProcessor
        # output queue:
        self.frame_queue = self.experiment.frame_dispatcher.gui_queue

        # Get the tracking parameters from the experiment class and connect
        # their change signal to update ROI position:
        self.track_params = self.experiment.tracking_method.params
        self.track_params.sigTreeStateChanged.connect(self.set_pos_from_tree)

    def initialise_roi(self):
        """ ROI is initialised separately, so it can first be defined in the
        child __init__.
        """
        try:
            # Add ROI to image and connect it to the function for updating
            # the relative params:
            self.display_area.addItem(self.roi)
            self.roi.sigRegionChangeFinished.connect(self.set_pos_from_roi)
        except AttributeError:
            print('No ROI defined in CameraSelection child')

    def set_pos_from_tree(self):
        """ Called when ROI position values are changed in the ParameterTree.
        Change the position of the displayed ROI:
        """
        pass

    def set_pos_from_roi(self):
        """ Called when ROI position values are changed in the displayed ROI.
        Change the position in the ParameterTree values.
        """
        pass


class CameraTailSelection(CameraSelection):
    """ Widget for select tail pts and monitoring tracking in embedded fish.
    """
    def __init__(self, experiment, **kwargs):
        """
        :param experiment:  experiment in which it is used.

        """

        super().__init__(experiment, **kwargs)

        # Draw ROI for tail selection:
        self.roi = pg.LineSegmentROI((self.track_params['tail_start'],
                                     (self.track_params['tail_start'][0] +
                                      self.track_params['tail_length'][0],
                                      self.track_params['tail_start'][1] +
                                      self.track_params['tail_length'][1])),
                                     pen=dict(color=(230, 40, 5),
                                              width=3))
        self.initialise_roi()

        # Prepare curve for plotting tracked tail position:
        self.tail_curve = pg.PlotCurveItem(pen=dict(color=(230, 40, 5),
                                                    width=3))
        self.display_area.addItem(self.tail_curve)

    def set_pos_from_tree(self):
        """ Go to parent for definition.
        """
        p1, p2 = self.roi.getHandles()
        p1.setPos(QPointF(*self.track_params['tail_start']))
        p2.setPos(QPointF(self.track_params['tail_start'][0] +
                          self.track_params['tail_length'][0],
                          self.track_params['tail_start'][1] +
                          self.track_params['tail_length'][1]))

    def set_pos_from_roi(self):
        """ Go to parent for definition.
        """
        p1, p2 = self.roi.getHandles()
        with self.track_params.treeChangeBlocker():
            self.track_params.param('tail_start').setValue((
                p1.x(), p1.y()))
            self.track_params.param('tail_length').setValue((
                p2.x() - p1.x(), p2.y() - p1.y()))

    def update_image(self):
        """ Go to parent for definition.
        """
        super().update_image()

        # Check for data to be displayed:
        if len(self.experiment.data_acc.stored_data) > 1:
            # Retrieve tail angles from tail:
            angles = self.experiment.data_acc.stored_data[-1][2:]

            # Get tail position and length from the parameters:
            start_x = self.track_params['tail_start'][1]
            start_y = self.track_params['tail_start'][0]
            tail_len_x = self.track_params['tail_length'][1]
            tail_len_y = self.track_params['tail_length'][0]
            tail_length = np.sqrt(tail_len_x ** 2 + tail_len_y ** 2)

            # Get segment length:
            tail_segment_length = tail_length / (len(angles) - 1)
            points = [np.array([start_x, start_y])]

            # Calculate tail points from angles and position:
            for angle in angles:
                points.append(points[-1] + tail_segment_length * np.array(
                    [np.sin(angle), np.cos(angle)]))
            points = np.array(points)
            self.tail_curve.setData(x=points[:, 1], y=points[:, 0])


class CameraEyesSelection(CameraSelection):
    """ Widget for select tail pts and monitoring tracking in embedded fish.
    """
    def __init__(self, experiment, **kwargs):
        """
        :param experiment:
        """

        super().__init__(experiment, **kwargs)

        # Draw ROI for eyes region selection:
        self.roi = pg.ROI(pos=self.track_params['wnd_pos'],
                          size=self.track_params['wnd_dim'],
                          pen=dict(color=(230, 40, 5),
                                   width=3))

        self.roi.addScaleHandle([0, 0], [1, 1])
        self.roi.addScaleHandle([1, 1], [0, 0])

        self.initialise_roi()

        # Prepare curves for displaying the eyes:
        self.curves_eyes = [pg.PlotCurveItem(pen=dict(color=(230, 40, 5),
                                                      width=3)),
                            pg.PlotCurveItem(pen=dict(color=(40, 230, 5),
                                                      width=3))]
        for c in self.curves_eyes:
            self.display_area.addItem(c)

    def set_pos_from_tree(self):
        """ Go to parent for definition.
        """
        self.roi.setPos(self.track_params['wnd_pos'], finish=False)
        self.roi.setSize(self.track_params['wnd_dim'])

    def set_pos_from_roi(self):
        """ Go to parent for definition.
        """
        # Set values in the ParameterTree:
        with self.track_params.treeChangeBlocker():
            self.track_params.param('wnd_dim').setValue(tuple(
                [int(p) for p in self.roi.size()]))
            self.track_params.param('wnd_pos').setValue(tuple(
                [int(p) for p in self.roi.pos()]))

    def update_image(self):
        """ Go to parent for definition.
        """
        super().update_image()
        if len(self.experiment.data_acc.stored_data) > 1:
            e = self.experiment.data_acc.stored_data[-1][1:]
            im = self.current_image
            if e[0] is not None:  # == e[0]:
                pos = self.track_params['wnd_pos']
                # im < self.track_params['threshold']).astype(np.uint8)
                imc = draw_ellipse(im,
                                   [((e[0]+pos[1], e[1]+pos[0]), tuple(e[2:4]), e[4]),
                                    ((e[5]+pos[1], e[6]+pos[0]), tuple(e[7:9]), e[9])],
                                   c=[(150, )*3, (150, )*3])

                self.image_item.setImage(imc)


class CameraViewCalib(CameraViewWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.points_calib = pg.ScatterPlotItem()
        self.display_area.addItem(self.points_calib)

    def show_calibration(self, calibrator):
        if calibrator.proj_to_cam is not None:
            camera_points = np.pad(calibrator.points, ((0, 0), (0, 1)),
                                   mode='constant', constant_values=1) @ calibrator.proj_to_cam.T

            points_dicts = []
            for point in camera_points:
                xn, yn = point[::-1]
                points_dicts.append(dict(x=xn, y=yn, size=8,
                                         brush=(210, 10, 10)))

            self.points_calib.setData(points_dicts)

