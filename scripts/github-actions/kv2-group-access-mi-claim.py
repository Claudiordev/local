import argparse
import os
import sys
parent_directory = os.path.abspath('./scripts')
sys.path.append(parent_directory)
from ruamel.yaml import YAML
from utils.logging.logging_config import logger

class MiClaims(object):

    def __init__(self, vaultEnvironment, systemName, managedIdentities, secretPaths):
        self.__vaultEnvironment = vaultEnvironment
        self.__systemName = systemName
        self.__managedIdentities = managedIdentities
        self.__secretPaths = secretPaths
        self.__kustomizationData= None
        self.__rootDirectory = os.getcwd()
        self.__yaml = YAML(typ=['rt', 'string'])
        self.__yaml.default_flow_style = False
        self.__secretEngine = self.__systemName + "-kv"

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
            return f

    def writeYaml(self,path):
        """
        """

        with open(path, "w") as f:
            self.__yaml.dump(self.__kustomizationData, f)

            return True

    def kustomization(self,kustomizationEntry):
        existing_resources_entries = list(self.__kustomizationData["resources"])
        if kustomizationEntry not in existing_resources_entries:
            existing_resources_entries.insert(len(self.__kustomizationData["resources"]),kustomizationEntry)
            self.__kustomizationData["resources"] = existing_resources_entries

    def updateFieldList(self,field,inputlist):
        """

        :return:
        """
        if len(self.__kustomizationData["spec"]["parameters"][f"{field}"]) > 0:
            extendedlist = list(self.__kustomizationData["spec"]["parameters"][f"{field}"])
            if extendedlist and extendedlist[0] is None:
                extendedlist.pop(0)
            extendedlist.extend(inputlist)
            extendedlist = list(set(extendedlist))
            self.__kustomizationData["spec"]["parameters"][f"{field}"] = extendedlist
        else:
            self.__kustomizationData["spec"]["parameters"][f"{field}"] = inputlist

    def parsePath(self, requestedSecretPaths):
        parsedPaths = []
        for secretPath in requestedSecretPaths:
            logger.info("Starting secret path: " + secretPath)
            secretPath = secretPath.strip().rstrip("/")
            if secretPath.endswith("*"):
                if len(secretPath.rstrip('*')) == 0:
                    secretPath = self.__secretEngine
                else:
                    if secretPath.endswith("/*"):
                        secretPath = secretPath.rstrip('/*')

            if secretPath != self.__secretEngine:
                if not secretPath.startswith(f"{self.__secretEngine}/") or not secretPath.startswith(f"{self.__secretEngine}/data/"): # != engine/ or engine/data/
                    if secretPath.startswith("/"): #and first character is /, so /engine-kv
                        secretPath = f"{self.__secretEngine}/data{secretPath}"
                    else:
                        secretPath = f"{self.__secretEngine}/data/{secretPath}"

            parsedPaths.append(secretPath)

        return parsedPaths


    def process(self,claim_type):
        """
            Generate internal group claim
        :return:
        """
        cwd = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/groups/internal"

        if claim_type == "internal-entity":
            cwd = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/internalEntities"
        elif claim_type == "kv2-group-access-mi":
            cwd = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/secret-engines/kv2/group-accesses-mi/" + self.__systemName + "-kv-int"
        # logger.info the current working directory
        logger.info("Current working directory: {0}".format(cwd))

        claim_path = cwd
        claim_exists=False

        if not self._claimPathExists(claim_path):
            logger.info(f"The directory for the {claim_type} claim {self.__systemName} does not exist.")
            logger.info(f"Creating the directory {self.__systemName}.")
            os.makedirs(claim_path,exist_ok=True)
            claim_path = f"{cwd}/{self.__systemName}-kv-int.yaml"
        else:
            claim_path = f"{cwd}/{self.__systemName}-kv-int.yaml"
            if claim_type != "internal-entity":
                logger.info(f"The directory for the {claim_type} claim {self.__systemName}-kv-int exists.")
            claim_exists = self._claimPathExists(claim_path)
            if claim_exists and claim_type != "internal-entity":
                logger.info(f"The claim for {self.__systemName}-kv-int exists, updating.")
            elif not claim_exists and claim_type != "internal-entity":
                logger.info(f"The claim {self.__systemName}-kv-int will be created.")

        kustomization_path = claim_path
        if not claim_exists:
            kustomization_path = f"templates/{claim_type}.yaml"

        self.loadTemplate(kustomization_path)

        managed_identities_list = [identity.strip() for identity in self.__managedIdentities.split(',')]
        secret_paths_list = [path.strip() for path in self.__secretPaths.split(',')] if self.__secretPaths else []

        logger.info("Updating the claim details.")
        # update the claim details
        if claim_type == "group":
            self.__kustomizationData["metadata"]["name"] = self.process_string(self.__systemName) + "-kv-int"
            self.__kustomizationData["spec"]["parameters"]["group"]["name"] = self.process_string(self.__systemName) + "-kv-int"
            self.__kustomizationData["spec"]["parameters"]["group"]["external"] = False
            if "objectId" in self.__kustomizationData["spec"]["parameters"]["group"]:
                del self.__kustomizationData["spec"]["parameters"]["group"]["objectId"]
        elif claim_type == "kv2-group-access-mi":
            self.__kustomizationData["metadata"]["name"] = self.process_string(self.__systemName) + "-kv-int"
            self.__kustomizationData["spec"]["parameters"]["systemName"]= self.process_string(self.__systemName)
            self.updateFieldList("managedIdentities",managed_identities_list)
            existingPaths = list(self.__kustomizationData["spec"]["parameters"]["readSecretPaths"])
            logger.info(len(existingPaths))
            if len(secret_paths_list) > 0:
                self.updateFieldList("readSecretPaths",self.parsePath(secret_paths_list))
            elif len(existingPaths) == 1:
                secret_paths_list.append(self.__secretEngine)
                self.updateFieldList("readSecretPaths",self.parsePath(secret_paths_list))
        elif claim_type == "internal-entity":
            for ie in managed_identities_list:
                claim_path = cwd + "/ie-" + ie + ".yaml"
                logger.info(f" Creating or updating the {claim_type} claim ie-{ie}.")
                self.__kustomizationData["metadata"]["name"] = "ie-" + ie
                self.__kustomizationData["spec"]["parameters"]["internalEntity"]["name"] = "ie-" + ie
                self.__kustomizationData["spec"]["parameters"]["internalEntity"]["objectId"] = ie

                if self.writeYaml(claim_path):
                    logger.info(f" {claim_type} Claim saved successfully.")
                    logger.info("---------------------------------")

        if claim_type != "internal-entity":
            if self.writeYaml(claim_path):
                logger.info(f" {claim_type} Claim saved successfully.")
                logger.info("---------------------------------")

        if claim_type == "group":
            kustomization_path = cwd + "/kustomization.yaml"
        elif claim_type == "kv2-group-access-mi":
            kustomization_path = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/secret-engines/kv2/group-accesses-mi/kustomization.yaml"
        elif claim_type == "internal-entity":
            kustomization_path = self.__rootDirectory + "/claims/azure/csm/" + self.__vaultEnvironment + "/internalEntities/kustomization.yaml"

        self.__yaml.indent(sequence=4, offset=2)

        self.loadTemplate(kustomization_path)

        kustomizationEntry = f"{self.__systemName}-kv-int.yaml"
        if claim_type == "kv2-group-access-mi":
            kustomizationEntry = f"{self.__systemName}-kv-int/{self.__systemName}-kv-int.yaml"

        elif claim_type == "internal-entity":
            for ie in managed_identities_list:
                kustomizationEntry = f"ie-{ie}.yaml"
                self.kustomization(kustomizationEntry)

        self.kustomization(kustomizationEntry)

        self.writeYaml(kustomization_path)

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
            secretPaths = args.secretPaths.strip() if args.secretPaths else None

            miClaims = MiClaims(vaultEnvironment, systemName, managedIdentities, secretPaths)

            # Process InternalGroupClaim
            miClaims.process('group')
            miClaims.process('kv2-group-access-mi')
            miClaims.process('internal-entity')
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)