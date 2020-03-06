#!/usr/bin/env python3
"""
Created on September 21 2019

@author: Melchior du Lac
@description: Extract the sink from an SBML into RP2 friendly format

"""
import argparse
import tempfile
import os
import logging
import shutil
import docker


##
#
#
def main(inputfile, 
         input_format,
         num_results,
         taxonomy_input,
         taxonomy_format,
         pathway_id,
         output):
    docker_client = docker.from_env()
    image_str = 'brsynth/rpselenzyme-standalone:dev'
    try:
        image = docker_client.images.get(image_str)
    except docker.errors.ImageNotFound:
        logging.warning('Could not find the image, trying to pull it')
        try:
            docker_client.images.pull(image_str)
            image = docker_client.images.get(image_str)
        except docker.errors.ImageNotFound:
            logging.error('Cannot pull image: '+str(image_str))
            exit(1)
    with tempfile.TemporaryDirectory() as tmpOutputFolder:
        shutil.copy(inputfile, tmpOutputFolder+'/input.dat')
        #command = #['/usr/local/envs/conda_selenzyme/bin/python',
        command = ['/home/tool_rpSelenzyme.py',
                   '-input',
                   '/home/tmp_output/input.dat',
                   '-output',
                   '/home/tmp_output/output.dat',
                   '-input_format',
                   str(input_format),
                   '-pathway_id',
                   str(pathway_id),
                   '-num_results',
                   str(num_results),
                   '-taxonomy_format',
                   str(taxonomy_format),
                   '-taxonomy_input',
                   str(taxonomy_input)]
        docker_client.containers.run(image_str, 
                command, 
                auto_remove=True, 
                detach=False, 
                volumes={tmpOutputFolder+'/': {'bind': '/home/tmp_output', 'mode': 'rw'}})
        shutil.copy(tmpOutputFolder+'/output.dat', output)


##
#
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser('Given an SBML, extract the reaction rules and pass them to Selenzyme REST service and write the results to the SBML')
    parser.add_argument('-input', type=str)
    parser.add_argument('-output', type=str)
    parser.add_argument('-input_format', type=str)
    parser.add_argument('-pathway_id', type=str, default='rp_pathway')
    parser.add_argument('-num_results', type=int, default=10)
    parser.add_argument('-taxonomy_format', type=str)
    parser.add_argument('-taxonomy_input', type=str)
    params = parser.parse_args()
    main(params.input, 
         params.input_format,
         params.num_results,
         params.taxonomy_input,
         params.taxonomy_format,
         params.pathway_id,
         params.output)
