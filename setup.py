import setuptools


setuptools.setup(
    name="needlestack",
    version="0.1.0-rc0",
    url="https://github.com/needlehaystack/needlestack",
    author="Cung Tran",
    author_email="minishcung@gmail.com",
    description="A distributed vector search microservice.",
    long_description=open("README.rst").read(),
    keywords="distributed nearest neighbors",
    license="Apache License 2.0",
    packages=setuptools.find_packages(),
    install_requires=["grpcio>=1.18.0", "numpy>=1.15.2", "protobuf>=3.6.1", "kazoo>=2.6.1"],
    extras_require={"faiss": ["faiss==1.5.3"], "gcs": ["google-cloud-storage==1.25.0"]},
    tests_require=["pytest", "pytest-cov"],
    setup_requires=["pytest-runner"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
