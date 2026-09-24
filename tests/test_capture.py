from ocr_tool.capture import crop_rect, screen_relative_rect


def test_selection_on_the_primary_screen_keeps_its_coordinates():
    assert screen_relative_rect((100, 50, 200, 100), (0, 0, 1536, 864)) == (
        100,
        50,
        200,
        100,
    )


def test_selection_on_a_second_screen_loses_the_screen_offset():
    assert screen_relative_rect(
        (1536 + 100, 50, 200, 100), (1536, 0, 1536, 864)
    ) == (100, 50, 200, 100)


def test_selection_crossing_a_screen_edge_is_clipped():
    assert screen_relative_rect((1500, 0, 200, 100), (0, 0, 1536, 864)) == (
        1500,
        0,
        36,
        100,
    )


def test_selection_outside_a_screen_is_none():
    assert screen_relative_rect((2000, 0, 100, 100), (0, 0, 1536, 864)) is None
    assert screen_relative_rect((0, 900, 100, 100), (0, 0, 1536, 864)) is None


def test_crop_rect_scales_logical_selection_to_device_pixels():
    # 控件 1536x864（逻辑），图 1920x1080（设备），比例 1.25
    assert crop_rect((100, 48, 200, 80), (1536, 864), (1920, 1080)) == (
        125,
        60,
        250,
        100,
    )


def test_crop_rect_is_identity_when_scales_match():
    assert crop_rect((10, 20, 30, 40), (800, 600), (800, 600)) == (10, 20, 30, 40)
