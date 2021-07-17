CC=jupiter
PYTHON=python3
FMT=black
PM=pip3

default: fmt
	$(CC) notebook

fmt:
	$(FMT) .

check:
	echo "Nothings yet"

dep:
	$(PM) install -r requirements.txt

env:
	$(PYTHON) -m venv .venv
	echo "Run the following command to access in the env"
	echo "source .venv/bin/activate"

clean:
	rm -rf .venv **/__p*
