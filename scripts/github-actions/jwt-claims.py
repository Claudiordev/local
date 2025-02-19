import argparse
import os
import sys
parent_directory = os.path.abspath('./scripts')
sys.path.append(parent_directory)
from ruamel.yaml import YAML
from utils.logging.logging_config import logger

class JwtClaims(object):

    def __init__(self, vaultEnvironment, systemName, managedIdentities, secretPaths):
        self.__vaultEnvironment = vaultEnvironment
        self.__systemName = systemName
        self.__managedIdentities = managedIdentities
        self.__secretPaths = secretPaths
        self.__kustomizationData= None
        self.__rootDirectory = os.getcwd()
        self.__yaml = YAML(typ=['rt', 'string'])
        self.__yaml.default_flow_style = False

    def _claimPathExists(self, path)-> bool:
        """
            Returns:
            bool: Returns True if the directory for path exists, otherwise False.
        """
        return os.path.exists(path)

    def process_string(self,input_string):
        """
            Replaces the irregular character strings.

        :return:
        """
        processed_string = (input_string.replace("/", "-").replace("#", "").replace("*", "-").replace(".", "-").replace("_", "-").replace("--", "-").replace(" ", "-"))

        return processed_string

    def loadTemplate(self, kustomization_path):
        """
            Open the yaml file for reading and writing

         """
        logger.info(f"Loading the kustomization data from {kustomization_path}.")

        with open(kustomization_path, "r+") as f:
            # load the kustomization data
            self.__kustomizationData = self.__yaml.load(f)

        return


    def processEntity(self,claim_type):
        """
            Generate internal group claim
        :return:
        """
        cwd = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/jwt"
        # logger.info the current working directory
        logger.info("Current working directory: {0}".format(cwd))

        claim_path = cwd + "/" + self.__systemName
        claim_exists=False

        if not self._claimPathExists(claim_path):
            logger.info(f"The directory for the claim {self.__systemName} does not exist.")
            logger.info(f"Creating the directory {self.__systemName}.")
            os.makedirs(claim_path,exist_ok=True)
            claim_path = f"{cwd}/{self.__systemName}/{self.__systemName}-{claim_type}.yaml"
        else:
            claim_path = f"{cwd}/{self.__systemName}/{self.__systemName}-{claim_type}.yaml"
            logger.info(f"The directory for the claim {self.__systemName} exists.")
            claim_exists = self._claimPathExists(claim_path)
            if claim_exists:
                logger.info(f"The claim for {self.__systemName} exists, updating.")
            else:
                logger.info(f"The claim {self.__systemName} will be created.")

        kustomization_path = claim_path
        if not claim_exists:
            kustomization_path = f"templates/jwt-{claim_type}.yaml"

        self.loadTemplate(kustomization_path)

        logger.info("Updating the claim details.")
        # update the claim details
        if claim_type == "internal-group":
            self.__kustomizationData["metadata"]["name"] = self.process_string(self.__systemName) + "-group"
            self.__kustomizationData["spec"]["parameters"]["group"]["name"] = self.__systemName + "-group"
            self.__kustomizationData["spec"]["parameters"]["group"]["policy"] = self.__systemName + "-policy"
        elif claim_type == "entity":
            self.__kustomizationData["metadata"]["name"] = self.process_string(self.__systemName) + "-entity"
            self.__kustomizationData["spec"]["parameters"]["entity"]["name"] = self.__systemName + "-entity"
        elif claim_type == "entity-alias":
            self.__kustomizationData["metadata"]["name"] = self.process_string(self.__systemName) + "-entity-alias"
            self.__kustomizationData["spec"]["parameters"]["alias"]["name"] = self.__systemName + "-entity-alias"
        elif claim_type == "vault-policy":
            self.__kustomizationData["metadata"]["name"] = self.process_string(self.__systemName) + "-policy"
            self.__kustomizationData["spec"]["parameters"]["policy"]["name"] = self.__systemName + "-policy"
            self.__kustomizationData["spec"]["parameters"]["policy"]["secretEngineName"] = self.__systemName

        logger.info(f"Updating the {self.__systemName}/{self.__systemName}.yaml")

        with open(claim_path, "w") as f:
            self.__yaml.dump(self.__kustomizationData, f)
            logger.info(f"JWT {claim_type} Claim saved successfully.")
            logger.info("---------------------------------")

        return


if __name__ == "__main__":
    try:
        # Check if the command is valid and call the appropriate function
        if sys.argv[1] == "create_claims":

            # Parse the command line arguments and create the group access configuration claim
            parser = argparse.ArgumentParser(description='Create internal group claim')
            parser.add_argument('command', choices=['create_claims'], help='Command to execute')
            parser.add_argument('--vaultEnvironment', required=True, help="Vault Environment (weu-qa, weu-prod, weu-dev)")
            parser.add_argument('--systemName', required=True, help="Name of the System")
            parser.add_argument('--managedIdentities', required=True, help='Managed identities')
            parser.add_argument('--secretPaths', required=False, help='Engine secret paths')

            args = parser.parse_args()

            vaultEnvironment = args.vaultEnvironment.strip()
            systemName = args.systemName.strip()
            managedIdentities = args.managedIdentities.strip()
            secretPaths = args.secretPaths.strip()

            jwtClaims = JwtClaims(vaultEnvironment, systemName, managedIdentities, secretPaths)

            # Process InternalGroupClaim
            jwtClaims.processEntity('internal-group')
            jwtClaims.processEntity('entity')
            jwtClaims.processEntity('entity-alias')
            jwtClaims.processEntity('vault-policy')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)