class SyncImageLoaderUseCase:
    def __init__(self, image_loader_service):
        self.image_loader_service = image_loader_service

    def execute(self):
        return self.image_loader_service.sync_all_images()