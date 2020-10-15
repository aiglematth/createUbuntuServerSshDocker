#!/usr/bin/env python3

#Auteur --> aiglematth
#But    --> Programme craaaaade pour pouvoir lancer X containers SSH que je peux utiliser pour faire mes tests ansible

#Imports
import docker
import os

#Fonctions
def exportSshKey(keyFile="~/.ssh/id_rsa.pub"):
	"""
	Exporte la clef ssh vers le rep courant
	:param keyFile: Le fichier clef .pub
	"""
	with open(keyFile, "r") as file:
		key = file.read()
	with open("id_rsa.pub", "w") as file:
		file.write(key)	

def removeSshKey():
	"""
	Exporte la clef ssh vers le rep courant
	:param keyFile: Le fichier clef .pub
	"""
	os.remove("id_rsa.pub")
	
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
		self.tag        = "myssh"
		self.docker     = docker.from_env()
		self.client     = docker.DockerClient()
		self.containers = []

	def build(self, keyFile="~/.ssh/id_rsa.pub"):
		"""
		Permet de build l'image de notre serveur ssh
		:param keyFile: La clef publique à utiliser
		"""
		try:
			self.docker.images.get(self.tag)
			return True
		except:
			pass

		exportSshKey(keyFile)	
		content = """
		FROM ubuntu:bionic

		RUN apt-get update && apt-get install openssh-server sudo -y
		RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 user 
		RUN echo 'user:user' | chpasswd
		RUN service ssh start
		RUN mkdir /home/ubuntu/.ssh

		COPY id_rsa.pub /home/ubuntu/.ssh/authorized_keys

		EXPOSE 22

		CMD ["/usr/sbin/sshd", "-D"]
		"""
		removeSshKey()
		return self.docker.images.build(path=".", tag=self.tag)

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

	args = parser.parse_args()

	if args.nombre:
		if args.kill_all:
			killAll()

		cluster = Cluster()
		if args.ssh_key:
			cluster.build(args.ssh_key)
		else:
			cluster.build
		cluster.run(args.nombre)
		print(cluster)

		if args.interactive:
			input("\n### Appuyer pour détruire les containers ###")
			cluster.kill()
	else:
		print(parser.format_help())
