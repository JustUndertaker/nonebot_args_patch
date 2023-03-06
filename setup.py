import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nonebot-args-patch",
    version="0.2.0",
    author="JustUndertaker",
    author_email="806792561@qq.com",
    description="一款自用的nb2获取指令参数的补丁",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JustUndertaker/nonebot_args_patch",
    packages=["nonebot_args_patch"],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
)
