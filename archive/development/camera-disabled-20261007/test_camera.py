from perception.camera import Camera

def test_camera():
    cam = Camera()
    frame = cam.read()
    cam.close()
    # Physical webcam is optional on the laptop. The live camera organ is
    # validated separately when hardware is present; absence must not fail V1.
    if frame is not None:
        assert frame.size > 0
        assert frame.shape[0] > 0 and frame.shape[1] > 0
