from os import getenv

from marshmallow.exceptions import (
    ValidationError as MarshmallowSchemaValidationError
)
from marshmallow_dataclass import dataclass

from booker.dto import DTOInvalidType, DataTransferClass


@dataclass
class Config(DataTransferClass):
    db_driver: str = 'postgres+psycopg2'
    db_host: str = 'db'
    db_port: int = 5432
    db_user: str = 'booker'
    db_password: str = 'booker'
    db_database: str = 'booker'
    http_host: str = '127.0.0.1'
    http_port: int = 8080
    zmq_proto: str = 'tcp'
    zmq_host: str = '127.0.0.1'
    zmq_port: int = 8081


    def with_environment(self) -> None:
        schema = type(self).Schema()

        try:
            updater = schema.load({
                'db_driver': getenv('DB_DRIVER'),
                'db_host': getenv('DB_HOST'),
                'db_port': getenv('DB_PORT'),
                'db_user': getenv('DB_USER'),
                'db_password': getenv('DB_PASSWORD'),
                'db_database': getenv('DB_DATABASE'),
                'http_host': getenv('HTTP_HOST'),
                'http_port': getenv('HTTP_PORT'),
                'zmq_proto': getenv('ZMQ_PROTO'),
                'zmq_host': getenv('ZMQ_HOST'),
                'zmq_port': getenv('ZMQ_PORT')
            })
        except MarshmallowSchemaValidationError as exception:
            logging.debug(exception)

            raise DTOInvalidType(f'Invalid payload type: {exception}')

        self.update(updater)
