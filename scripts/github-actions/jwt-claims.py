import argparse
import os
import sys
parent_directory = os.path.abspath('./scripts')
sys.path.append(parent_directory)
from ruamel.yaml import YAML
from utils.logging.logging_config import logger
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class JwtClaims(object):

    def __init__(self, vaultEnvironment, systemName, vaultEngine, managedEntities):
        self.__vaultEnvironment = vaultEnvironment
        self.__systemName = systemName
        self.__vaultEngine = vaultEngine
        self.__managedEntities = managedEntities
        self.__kustomizationData= None
        self.__rootDirectory = os.getcwd()
        self.__yaml = YAML(typ=['rt', 'string'])
        self.__yaml.default_flow_style = False

    def processGroupClaim(self):
        """
            Generate internal group claim
        :return:
        """
        cwd = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/auth-methods/jwt"
        # logger.info the current working directory
        logger.info("Current working directory: {0}".format(cwd))

        claim_path = cwd + "/" + self.__systemName
        claim_exists=False

        if not self._claimPathExists(claim_path):
            logger.info(f"The directory for the claim {self.__systemName} does not exist.")
            logger.info(f"Creating the directory {self.__systemName}.")
            os.makedirs(claim_path,exist_ok=True)
            claim_path = f"{cwd}/{self.__systemName}/{self.__systemName}.yaml"
        else:
            claim_path = f"{cwd}/{self.__systemName}/{self.__systemName}.yaml"
            logger.info(f"The directory for the claim {self.__systemName} exists.")
            claim_exists = self._claimPathExists(claim_path)
            if claim_exists:
                logger.info(f"The claim for {self.__systemName} exists, updating.")
            else:
                logger.info(f"The claim {self.__systemName} will be created.")

if __name__ == "__main__":
    try:
        # Check if the command is valid and call the appropriate function
        if sys.argv[1] == "create_internal_group_claim":

            # Parse the command line arguments and create the group access configuration claim
            parser = argparse.ArgumentParser(description='Create internal group claim')
            parser.add_argument('command', choices=['create_internal_group_claim'], help='Command to execute')
            parser.add_argument('--vaultEnvironment', required=True, help="Vault Environment (weu-qa, weu-prod, weu-dev)")
            parser.add_argument('--systemName', required=True, help="Name of the System")
            parser.add_argument('--vaultEngine', required=True, help="Vault Secret Engine")
            parser.add_argument('--managedEntities', required=True, help='Managed entities')

            args = parser.parse_args()

            vaultEnvironment = args.vaultEnvironment.strip()
            vaultEngine = args.vaultEngine.strip()
            systemName = args.systemName.strip()
            managedEntities = args.managedEntities.strip()

            jwtClaims = JwtClaims(vaultEnvironment, systemName, vaultEngine, managedEntities)

            # Process InternalGroupClaim
            jwtClaims.processGroupClaim()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)