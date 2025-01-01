# URL to image

This service will be used to take a picture of a url thru service. They will be cached for frequent usage. Can be invalidated by sending a delete request.

## Usage

### How to take a image of a website

```
curl -s http://localhost:8080/url2image/<url>?<request parameters>
```

1. URL

   Examples

   ### Secured URLs

   http://localhost:8080/url2image/https/www.google.com

   ### Unsecured URLs

   http://localhost:8080/url2image/http/182.3.44.22/page/id/001

   ### Un specified protocol scheme defaults to https

   http://localhost:8080/url2image/www.mysite.com/page/id/123-34-22

   **Currently port number is not supported in the url**

2. Request Parameters

   1. **device** - Specifies the type of the device the following are the allowed values and their respectice screen sizes. Default value is "DESKTOP".

      | Value            | Description                  | Size (Width x Height) in pixels |
      | ---------------- | ---------------------------- | ------------------------------- |
      | MOBILE           | Mobile portrait orientation  | 480 x 640                       |
      | MOBILE_LANDSCAPE | Mobile landscape orientation | 640 x 480                       |
      | TABLET           | Tablet portrait orientation  | 675 x 960                       |
      | TABLET_LANDSCAPE | Tablet landscape orientation | 960 x 750                       |
      | **DESKTOP**      | **Desktop screen (Default)** | **1280 x 1024**                 |
      | WIDE             | Wide screen                  | 1920 x 1080                     |
      | QHD              | Quad High Definition Screen  | 2560 x 1440                     |
      | 4K               | 4K Screen                    | 3840 x 2160                     |

   1. **deviceWidth** - Specifies the width of the device the url has to be rendered in pixels. When width and height are specified the previous parameter device is ignored.

   1. **deviceHeight** - Specifies the height of the device the url has to be rendred in pixels. When width and height are specified the parameter device is ignored.

   1. **imageType** - Specifies the type of the image to be generated, png or jpeg or webp.

      | Value    | Description                             |
      | -------- | --------------------------------------- |
      | **WEBP** | **Webp format (default)**               |
      | PNG      | Portable Network Graphics format        |
      | JPEG     | Joint Photographic Experts Group format |

   1. **imageSizeType** - Specifies the type of the image size to be generated based on device type or width and height.

      | Value     | Description                                                | Size (Width x Height) in pixels         |
      | --------- | ---------------------------------------------------------- | --------------------------------------- |
      | **THUMB** | **Thumbnail size (default)**                               | **320 x 180**                           |
      | THUMBX2   | Big Thumbnail size                                         | 640 x 320                               |
      | ORIGINAL  | Based on the device size                                   | Dynamic based on the size of the device |
      | FULL      | Full Page based on the device width (not implemented)      | Dynamic based on the size of device     |
      | FULLXHALF | Like full page but half the actual sizes (not implemented) | Dynamic based on the size of device     |

   1. **imageWidth** - Specifies the width of the image in pixel. When width and height are specified the imageSizeType is ignored.

   1. **imageHeight** - Specifies the height of the image in pixel. When width and height are specified the imageSizeType is ignored.

   1. **imageBandColor** - When the image size is not matching the aspect ratio of the device type then the image is centered. It makes transparent in the case of PNG and WEBP format when the image is centered but it defaults to black in case of JPEG. If the color is specified in the format of HTML HEX color code it will be used.

   1. **cacheControl** - Default cache control is **"public, max-age=604800"**, but if you specify a different option that is used. If the cacheControl contains **"must-revalidate"**, an Etag is generated and honored with If-None-Match.

   1. **waitTime** - Wait time determines how many milli seconds the thread needs to wait before taking a screenshot. By default 0 seocnds.

### How to invalidate the cache of a url image that is already taken

```
curl -s -X DELETE http://localhost:8080/url2image/<url>?<request parameters>
```

1.  URL and Request parameters has to be exactly same as before while taking an image of a url to invalidate the cache.
2.  waitTime is the only parameter that is not considered to check the uniqueness of the request while invalidating.

### How to invalidate the entire cache

```
curl -s -X DELETE http://localhost:8080/url2image/internal/all
```

## Configuration

Before getting into configuration here is a birds eye view of how this service works. It uses ChromeDriver to take images of a url. It uses caffeine cache to cache and a persistent disk to a given location. None of the persisted images are ever deleted unless they are evicted. It works like a read thru cache, when a particular url with the parameters is not cached in memory, it checks the persistence location. If it is not available in either locations then the actual image is created and persisted in both memory and on the disk.

Create an external application.properites file and override the default values.

1.  allowed.domains

    A comma separated value with list of domains from which you can take an image of a url. Default allows all domains.

2.  chromedriver

    Path to the installed chrome driver. Default is /usr/bin/chromedriver.

3.  fileCachePath

    Path to the file cache where all the images are stored. Defualt value is /tmp/ehcache.
