from typing import Any, Dict, List, Optional
import json
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from safe.config import config

engine = db.create_engine(f"sqlite:///{config['path']['database']}")
Base = declarative_base()


class Credential(Base):
    __tablename__ = 'credentials'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    items = db.Column(db.LargeBinary)


class Database:
    """Class used to interact with the database.

    Args:
        pswd: Master password used for encryption.
    """

    def __init__(self, pswd: str):
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        self._pswd = pswd
        self.session = Session()

    def close(self):
        self.session.close()

    def _derive_key(self, salt: bytes) -> bytes:
        """Generates an encryption key from password.

        Args:
            salt: Random bytes
        """
        return PBKDF2(self._pswd, salt, 32)

    def _encrypt(self, data: Any) -> bytes:
        """Encrypts data with the master password.

        Args:
            data: Data to encrypt [str, dict]

        Returns:
            Ciphertext
        """
        if type(data) is not str:
            data = json.dumps(data)

        salt = get_random_bytes(16)
        cipher = AES.new(self._derive_key(salt), AES.MODE_CBC)
        ciphertext = cipher.encrypt(pad(data.encode(), AES.block_size))
        return salt + cipher.iv + ciphertext

    def _decrypt(self, ciphertext: bytes, json_=False) -> str | Any:
        """Decrypts the ciphertext generated by Database._encrypt method.

        Args:
            ciphertext: Encrypted data
            json_: Whether to return json parsed object.

        Returns:
            Decrypted data
        """
        salt = ciphertext[:16]
        iv = ciphertext[16:32]
        cipher = AES.new(self._derive_key(salt), AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(
            ciphertext[32:]), AES.block_size).decode()
        if json_:
            return json.loads(plaintext)
        return plaintext

    @property
    def count(self) -> int:
        return self.session.query(Credential).count()

    def exists(self, name: str) -> bool:
        credential = self.session.query(
            Credential).filter_by(name=name).first()
        return credential is not None

    def insert(self, name: str, items: Dict[str, str]) -> None:
        """Adds new credential to the database.

        Args:
            name: Name of the credential.
            items: Key-value pair credentials.
        """
        credential = Credential(name=name, items=self._encrypt(items))
        self.session.add(credential)
        self.session.commit()

    def get(self, name: str) -> Optional[Credential]:
        """Retrives a single credential from the database.

        Args:
            name: Name of the credential.
        """
        credential = self.session.query(
            Credential).filter_by(name=name).first()
        if credential is not None:
            decrypted_items = self._decrypt(credential.items, True)
            credential.items_dict = decrypted_items
            return credential

    def get_all(self) -> List[Credential]:
        """Retrives all the credential in the database."""
        credentials = self.session.query(Credential).all()
        for credential in credentials:
            decrypted_items = self._decrypt(credential.items, True)
            credential.items_dict = decrypted_items
        return credentials

    def update(self, credential: str | Credential, new_name: str, new_items: Dict[str, str]) -> None:
        """Updates an existing credential in the database.

        Args:
            credential: Instance of Credential or name of the credential.
            new_name: New name for the credential.
            new_items: New items for the credential.
        """
        if type(credential) is str:
            credential = self.get(credential)
        if credential is not None:
            credential.name = new_name
            credential.items = self._encrypt(new_items)
            self.session.commit()

    def delete(self, credential: str | Credential) -> None:
        """Deletes an existing credential in the database.

        Args:
            credential: Instance of Credential or name of the credential.
        """
        if type(credential) is str:
            credential = self.get(credential)
        if credential is not None:
            self.session.delete(credential)
            self.session.commit()

    def change_pswd(self, new_pswd: str) -> None:
        """Changes the password used to encrypt the credentials.

        Args:
            new_pswd: New password
        """
        credentials = self.get_all()
        self._pswd = new_pswd

        for credential in credentials:
            credential.items = self._encrypt(credential.items_dict)
        self.session.commit()