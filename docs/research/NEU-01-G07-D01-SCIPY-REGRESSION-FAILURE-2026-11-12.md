# NEU-01-G07-CI-D01 — SciPy dependency omitted from the general regression environment

**12 November 2026.** This post-G07 engineering correction is separate from the original source protocol, first source workflow and immutable artifact. The first G07 dedicated workflow #43332821093 succeeded because it explicitly installed SciPy, NumPy and pytest. The full repository Research regression tests at the implementation head **#43332820847** and archived head **#43333083443** did NOT succeed. The inspected collection error was precisely: ModuleNotFoundError: No module named 'scipy' while importing tests/test_neu01_g07_eeglab_pilot.py. These failures are preserved, not recast as science or deleted.

Root cause: experiments/neu01_g07_eeglab_pilot.py and its test fixture import scipy.io, but pyproject.toml declared only NumPy and NetworkX as core dependencies, with pytest as a dev extra. The general regression workflow installs the declared project using editable dev extras, not the G07 bespoke dependency command, so tests could not even be collected. The original authenticated .set bytes and first source result are unaffected.

The exact proposed and executed fix changes **only one project dependency line**, adding scipy>=1.11,<2 to project.dependencies. This is required for every environment that imports the G07 source reader, rather than suppressing tests with an unjustified skip. No old source artifact, result, subject, source URI, schema, numerical outcome, protocol or experiment code is changed. A new full repository matrix must actually pass on Python 3.11 and 3.12 before claiming general regression repaired. No original derivative object download is needed for this change.

Evidence: original G07 source https://github.com/DevHabito/relational-persistence/actions/runs/43332821093; failed main regression https://github.com/DevHabito/relational-persistence/actions/runs/43332820847 and failed archived regression https://github.com/DevHabito/relational-persistence/actions/runs/43333083443.

**This is a transparent dependency/install correction following a real negative CI result, not an experiment amendment or a new observation about EEG.**
