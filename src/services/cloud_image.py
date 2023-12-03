import hashlib

import cloudinary
import cloudinary.uploader

from src.conf.config import settings


class CloudImage:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    @staticmethod
    def generate_name_avatar(email: str):
        """
        The generate_name_avatar function takes an email address as input and returns a unique name for the user.
        The function uses the SHA256 hash of the email address to generate a 12-character string, which is then used to create
        a Docker image name in this format: fastapi/{name}. The generated image name will be used by FastAPI to run your code.

        :param email: str: Specify the type of the parameter
        :return: A string, so it is a valid function to use in the avatar_url parameter
        :doc-author: Trelent
        """
        name = hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]
        return f"fastapi/{name}"

    @staticmethod
    def upload(file, public_id: str):
        """
        The upload function takes a file and public_id as arguments.
            The function then uploads the file to Cloudinary with the given public_id.
            If there is already an image with that id, it will be overwritten.

        :param file: Specify the file to upload
        :param public_id: str: Specify the public id of the image
        :return: A dict
        :doc-author: Trelent
        """
        r = cloudinary.uploader.upload(
            file, public_id=public_id, overwrite=True)
        return r

    @staticmethod
    def get_url_for_avatar(public_id, r):
        """
        The get_url_for_avatar function takes a public_id and an optional resource dictionary.
        It returns the URL for the avatar image, which is a 250x250px crop of the original image.

        :param public_id: Specify the image to be used
        :param r: Get the version of the image
        :return: A url for the avatar image
        :doc-author: Trelent
        """
        src_url = cloudinary.CloudinaryImage(public_id) \
            .build_url(width=250, height=250, crop='fill', version=r.get('version'))
        return src_url
