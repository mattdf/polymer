PYTHON3=python3
PROJNAME=polymerizer
MODNAME=turbopotato

all: api

api:
	$(PYTHON3) -muvicorn $(MODNAME).api:app --reload --host 0.0.0.0 --port 8000

py:
	PYTHONPATH=. $(PYTHON3)

clean:
	rm -rf $(MODNAME)/__pycache__ __pycache__ .npm

python-requirements:
	$(PYTHON3) -mpip install --user -r requirements.txt

docker-build:
	docker build -t $(PROJNAME)/analyzer:latest -f Dockerfile.analyzer .

docker-shell:
	docker run --rm -ti -v `pwd`:/src -u `id -u`:`id -g` -h $(PROJNAME) -e HOME=/src -e HISTFILESIZE=0 -w /src $(PROJNAME)/analyzer:latest /bin/bash

docker-clean:
	docker rmi $(PROJNAME)/analyzer:latest
