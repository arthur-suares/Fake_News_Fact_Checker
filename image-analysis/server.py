import base64
import binascii

from mcp.server.fastmcp import FastMCP

from service import analyze_image as analyze_image_service


MAX_IMAGE_BYTES = 10 * 1024 * 1024
mcp = FastMCP("image-analysis")


@mcp.tool()
def analyze_image(image_base64: str, mime_type: str, text: str | None = None) -> dict:
    """Describe an image and optionally compare its visible content with a claim.

    Send the image bytes encoded as Base64 and its MIME type, such as image/jpeg
    or image/png. The analysis does not establish whether a claim is true.
    """
    try:
        image = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("image_base64 must contain valid Base64 data") from error

    if len(image) > MAX_IMAGE_BYTES:
        raise ValueError("The image must not exceed 10 MiB")

    return analyze_image_service(image, text=text, media_type=mime_type)


if __name__ == "__main__":
    mcp.run(transport="stdio")