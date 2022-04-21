import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="retroBot",
    version="0.1.12",
    author="retrontology",
    author_email="retrontology@hotmail.com",
    description="A Twitch IRC bot integrating twitchAPI and irc",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/retrontology/retroBot",
    project_urls={
        "Bug Tracker": "https://github.com/retrontology/retroBot/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPL-3.0 License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)