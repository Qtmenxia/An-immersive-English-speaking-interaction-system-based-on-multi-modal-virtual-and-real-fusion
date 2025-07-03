from setuptools import setup, find_packages
setup(
    name='agent_vr_Assistant',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'autogen_agentchat==0.2.37',
        'Flask==3.0.3',
        'flask_sock==0.7.0',
        'setuptools==75.1.0',
        'websockets==13.1',
    ],
    entry_points={
        'console_scripts': [
            'Start_Agent_Service = app.App:main',
        ],
    },
)
