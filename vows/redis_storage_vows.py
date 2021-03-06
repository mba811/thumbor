#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/globocom/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com

import redis
from pyvows import Vows, expect

from thumbor.storages.redis_storage import Storage as RedisStorage
from thumbor.context import Context
from thumbor.config import Config
from fixtures.storage_fixture import IMAGE_URL, IMAGE_BYTES, get_server


class RedisDBContext(Vows.Context):
    def setup(self):
        self.connection = redis.Redis(port=6668,
                                      host='localhost',
                                      db=0,
                                      password='hey_you')


@Vows.batch
class RedisStorageVows(RedisDBContext):
    class CanStoreImage(Vows.Context):
        def topic(self):
            config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
            storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % 1, IMAGE_BYTES)
            return self.parent.connection.get(IMAGE_URL % 1)

        def should_be_in_catalog(self, topic):
            expect(topic).not_to_be_null()
            expect(topic).not_to_be_an_error()

    class KnowsImageExists(Vows.Context):
        def topic(self):
            config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
            storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % 9999, IMAGE_BYTES)
            return storage.exists(IMAGE_URL % 9999)

        def should_exist(self, topic):
            expect(topic.exception()).not_to_be_an_error()
            expect(topic.result()).to_be_true()

    class KnowsImageDoesNotExist(Vows.Context):
        def topic(self):
            config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
            storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
            return storage.exists(IMAGE_URL % 10000)

        def should_not_exist(self, topic):
            expect(topic.exception()).not_to_be_an_error()
            expect(topic.result()).to_be_false()

    class CanRemoveImage(Vows.Context):
        def topic(self):
            config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
            storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % 10001, IMAGE_BYTES)
            storage.remove(IMAGE_URL % 10001)
            return self.parent.connection.get(IMAGE_URL % 10001)

        def should_not_be_in_catalog(self, topic):
            expect(topic).not_to_be_an_error()
            expect(topic).to_be_null()

        class CanReRemoveImage(Vows.Context):
            def topic(self):
                config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
                storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
                return storage.remove(IMAGE_URL % 10001)

            def should_not_be_in_catalog(self, topic):
                expect(topic).not_to_be_an_error()
                expect(topic).to_be_null()

    class CanGetImage(Vows.Context):
        def topic(self):
            config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
            storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))

            storage.put(IMAGE_URL % 2, IMAGE_BYTES)
            return storage.get(IMAGE_URL % 2)

        def should_not_be_null(self, topic):
            expect(topic.result()).not_to_be_null()
            expect(topic.exception()).not_to_be_an_error()

        def should_have_proper_bytes(self, topic):
            expect(topic.result()).to_equal(IMAGE_BYTES)

    class HandleErrors(Vows.Context):
        class CanRaiseErrors(Vows.Context):
            @Vows.capture_error
            def topic(self):
                config = Config(
                    REDIS_STORAGE_SERVER_PORT=300,
                    REDIS_STORAGE_SERVER_PASSWORD='nope',
                    REDIS_STORAGE_IGNORE_ERRORS=False
                )
                storage = RedisStorage(
                    context=Context(
                        config=config,
                        server=get_server('ACME-SEC')
                    ),
                    shared_client=False
                )

                return storage.exists(IMAGE_URL % 2)

            def should_throw_an_exception(self, topic):
                expect(
                    topic
                ).to_be_an_error_like(redis.RedisError)

        class IgnoreErrors(Vows.Context):
            def topic(self):
                config = Config(
                    REDIS_STORAGE_SERVER_PORT=300,
                    REDIS_STORAGE_SERVER_PASSWORD='nope',
                    REDIS_STORAGE_IGNORE_ERRORS=True
                )
                storage = RedisStorage(
                    context=Context(
                        config=config,
                        server=get_server('ACME-SEC')
                    ),
                    shared_client=False
                )

                return storage

            def should_return_false(self, storage):
                result = storage.exists(IMAGE_URL % 2)
                expect(result.result()).to_equal(False)
                expect(result.exception()).not_to_be_an_error()

            def should_return_none(self, storage):
                result = storage.get(IMAGE_URL % 2)
                expect(result.result()).to_equal(None)
                expect(result.exception()).not_to_be_an_error()

    class CryptoVows(Vows.Context):
        class RaisesIfInvalidConfig(Vows.Context):

            @Vows.capture_error
            def topic(self):
                config = Config(
                    REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you',
                    STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
                storage = RedisStorage(Context(config=config, server=get_server('')))
                storage.put(IMAGE_URL % 3, IMAGE_BYTES)
                storage.put_crypto(IMAGE_URL % 3)

            def should_be_an_error(self, topic):
                expect(topic).to_be_an_error_like(RuntimeError)
                expect(topic).to_have_an_error_message_of(
                    "STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True if no SECURITY_KEY specified"
                )

        class GettingCryptoForANewImageReturnsNone(Vows.Context):
            def topic(self):
                config = Config(
                    REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you',
                    STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True
                )
                storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
                return storage.get_crypto(IMAGE_URL % 9999)

            def should_be_null(self, topic):
                expect(topic.result()).to_be_null()

        class DoesNotStoreIfConfigSaysNotTo(Vows.Context):
            def topic(self):
                config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
                storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
                storage.put(IMAGE_URL % 5, IMAGE_BYTES)
                storage.put_crypto(IMAGE_URL % 5)
                return storage.get_crypto(IMAGE_URL % 5)

            def should_be_null(self, topic):
                expect(topic.result()).to_be_null()

        class CanStoreCrypto(Vows.Context):
            def topic(self):
                config = Config(
                    REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you',
                    STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True
                )
                storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))

                storage.put(IMAGE_URL % 6, IMAGE_BYTES)
                storage.put_crypto(IMAGE_URL % 6)
                return storage.get_crypto(IMAGE_URL % 6)

            def should_not_be_null(self, topic):
                expect(topic.result()).not_to_be_null()
                expect(topic.exception()).not_to_be_an_error()

            def should_have_proper_key(self, topic):
                expect(topic.result()).to_equal('ACME-SEC')

    class DetectorVows(Vows.Context):
        class CanStoreDetectorData(Vows.Context):
            def topic(self):
                config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
                storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
                storage.put(IMAGE_URL % 7, IMAGE_BYTES)
                storage.put_detector_data(IMAGE_URL % 7, 'some-data')
                return storage.get_detector_data(IMAGE_URL % 7)

            def should_not_be_null(self, topic):
                expect(topic.result()).not_to_be_null()
                expect(topic.exception()).not_to_be_an_error()

            def should_equal_some_data(self, topic):
                expect(topic.result()).to_equal('some-data')

        class ReturnsNoneIfNoDetectorData(Vows.Context):
            def topic(self):
                config = Config(REDIS_STORAGE_SERVER_PORT=6668, REDIS_STORAGE_SERVER_PASSWORD='hey_you')
                storage = RedisStorage(Context(config=config, server=get_server('ACME-SEC')))
                return storage.get_detector_data(IMAGE_URL % 10000)

            def should_not_be_null(self, topic):
                expect(topic.result()).to_be_null()
