from setuptools import setup, find_packages

setup(
    name='mcqgenerator',
    version='0.0.1',
    author='Indra suthar',
    author_email='indrasuthar14@gmail.com',
    install_requires=['openai', 'python-dotenv', 'langchain', 'streamlit', 'PyPDF2'],
    packages=find_packages()
)
