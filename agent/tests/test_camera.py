from perception.camera import Camera

def test_camera():
    cam = Camera()
    frame = cam.read()
    cam.close()
    assert frame is not None
    assert frame.shape[0] > 0 and frame.shape[1] > 0
