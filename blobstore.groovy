// https://github.com/savoirfairelinux/ansible-nexus3-oss/tree/master/files/groovy
import groovy.json.JsonSlurper

parsed_args = new JsonSlurper().parseText(args)

existingBlobStore = blobStore.getBlobStoreManager().get(parsed_args.name)
if (existingBlobStore == null) {
    blobStore.createFileBlobStore(parsed_args.name, parsed_args.path)
}
