package com.modlix.urlscreenshot.dto;

import java.io.Serializable;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@AllArgsConstructor
@EqualsAndHashCode
public class URLImage implements Serializable {
    private static final long serialVersionUID = 1L;

    private byte[] data;
    private String url;
    private URLImageParameters parameters;
    private long timestamp;
}