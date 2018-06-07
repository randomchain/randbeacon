==========
randbeacon
==========

A Trustworthy Public Randomness Beacon, build to be scalable and highly distributable.
Uses ZeroMQ_ for inter component communication.

Dependencies are managed with pipenv_, to install run::

    pipenv --three install

Use tmux_ and tmuxp_ to run a local instance::

    tmuxp load .

Change ``.tmuxp.yaml`` to configre the local beacon instance.

* Free software: MIT license


.. _ZeroMQ: https://zeromq.org
.. _pipenv: https://docs.pipenv.org
.. _tmux: https://github.com/tmux/tmux
.. _tmuxp: https://tmuxp.git-pull.com
