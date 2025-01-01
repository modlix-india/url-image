package com.modlix.urlscreenshot.enums;

public enum DeviceType {

    MOBILE(480, 640),
    MOBILE_LANDSCAPE(640, 480),
    TABLET(675, 960),
    TABLET_LANDSCAPE(960, 750),
    DESKTOP(1280, 1024),
    WIDE(1920, 1080),
    QHD(2560, 1440),
    K4(3840, 2160);

    DeviceType(int width, int height) {
        this.width = width;
        this.height = height;
    }

    private final int width;
    private final int height;

    public int getWidth() {
        return width;
    }

    public int getHeight() {
        return height;
    }
}
