from flask import Response, make_response


def make_pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    """
    Create a Flask response object for a PDF file.

    Args:
        pdf_bytes (bytes): The PDF file content as bytes.
        filename (str): The name of the file to be used in the response.

    Returns:
        Response: A Flask response object with the PDF content and appropriate headers.
    """
    response = make_response(pdf_bytes)
    response.headers.set("Content-Type", "application/pdf")
    response.headers.set("Content-Disposition", "inline", filename=filename)
    return response
