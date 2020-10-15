#!/usr/bin/env python3

#Auteur --> aiglematth
#But    --> Programme craaaaade pour pouvoir lancer X containers SSH que je peux utiliser pour faire mes tests ansible

#Imports
import docker
import os

#Fonctions
def createContext():
	"""
	On se place dans un dossier où on peut faire touuut ce qu'on veut
	"""
	try:
		os.mkdir("/tmp/.createCluster")
	except:
		pass
	os.chdir("/tmp/.createCluster")

def exportSshKey(keyFile=f"~/.ssh/id_rsa.pub"):
	"""
	Exporte la clef ssh vers le rep courant
	:param keyFile: Le fichier clef .pub
	"""
	print("KEEE", keyFile)
	with open(keyFile, "r") as file:
		key = file.read()
	with open("id_rsa.pub", "w") as file:
		file.write(key)	
	
def killAll():
	"""
	Arrête tout les containers de la machine
	"""
	dock = docker.from_env()
	for container in dock.containers.list():
		container.kill()

#Classes
class Cluster():
	"""
	Classe qui va nous permettre de créer et de détruire un cluster de machines joignables en ssh
	"""
	def __init__(self):
		"""
		Constructeur de la classe
		"""
		createContext()
		self.tag        = "myssh"
		self.docker     = docker.from_env()
		self.client     = docker.DockerClient()
		self.containers = []

	def build(self, keyFile="~/.ssh/id_rsa.pub"):
		"""
		Permet de build l'image de notre serveur ssh
		:param keyFile: La clef publique à utiliser
		"""
		exportSshKey(keyFile)	
		content = """
		FROM ubuntu:bionic

		RUN apt-get update && apt-get install openssh-server sudo -y
		RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 user
		RUN sed -i "s/.*PermitRootLogin.*/PermitRootLogin yes/g" /etc/ssh/sshd_config
		RUN echo 'user:user' | chpasswd
		RUN service ssh start
		RUN mkdir /home/ubuntu/.ssh
		RUN mkdir /root/.ssh

		COPY id_rsa.pub /home/ubuntu/.ssh/authorized_keys
                COPY id_rsa.pub /root/.ssh/authorized_keys


		EXPOSE 22

		CMD ["/usr/sbin/sshd", "-D"]
		"""
		with open("Dockerfile", "w") as file:
			file.write(content)
		self.docker.images.build(path=".", tag=self.tag)


	def run(self, nbr):
		"""
		Lance nos containers
		:param nbr: Le nombre de containers à lancer
		"""
		for _ in range(nbr):
			container = self.docker.containers.run(self.tag, detach=True)
			self.containers.append(container)

	def kill(self):
		"""
		Kill tout les containers
		"""
		for container in self.containers:
			container.kill()

	def __str__(self):
		"""
		On met nos host dans un format yml
		"""
		content = "---\nall:\n"
		for container in self.containers:
			real     = self.client.containers.get(container.short_id)
			content += f"    {real.attrs['NetworkSettings']['IPAddress']}:\n"
		return content

if __name__ == "__main__":
	from argparse import *

	parser = ArgumentParser(description="Petit outil qui lance des containers SSH")
	parser.add_argument("--nombre", type=int, help="Précise le nombre de containers")
	parser.add_argument("--ssh-key", type=str, help="Précise le chemin vers la clef publique à utiliser")
	parser.add_argument("--interactive", action="store_true", help="Se lance en premier plan")
	parser.add_argument("--kill-all", action="store_true", help="Kill TOUT les containers au début du programme")
	parser.add_argument("--verbose", action="store_true", help="Permet d'afficher un peut de texte nous renseignant sur la bonne exe du programme")

	args = parser.parse_args()

	if args.kill_all:
		if args.verbose: print("### KILLALL ###")		
		killAll()

	if args.nombre != None and args.nombre > 0:

		cluster = Cluster()
		if args.ssh_key:
			if args.verbose: print(f"### BUILD WITH {args.ssh_key} KEY ###")		
			cluster.build(args.ssh_key)
		else:
			if args.verbose: print(f"### BUILD WITH AUTO KEY ###")		
			cluster.build()
		
		if args.verbose: print(f"### RUN {args.nombre} CONTAINERS ###")		
		cluster.run(args.nombre)
		print(cluster)

		if args.interactive:
			input("\n### Appuyer pour détruire les containers ###")
			cluster.kill()
	
	if not args.nombre and not args.kill_all:
		print(parser.format_help())
