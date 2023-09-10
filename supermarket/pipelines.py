# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import uuid
import psycopg2
import colorama

from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()


class SupermarketPipeline:

    def __init__(self) -> None:
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")

        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=database,
        )
        self.cursor = self.connection.cursor()

    def process_item(self, item, spider):
        uuid_ptr_id = uuid.uuid4()
        name = item.get("name")
        description = item.get("description")
        brand = item.get("brand")
        image = item.get("image")
        url = item.get("url")
        items_sold = item.get("items_sold")
        ratings = item.get("ratings")
        condition = item.get("condition")
        original_price = item.get("original_price")
        price = item.get("price")
        shipping_charges = item.get("shipping_charges")
        source = item.get("source")
        discount = item.get("discount")
        type = item.get("type")

        if len(price) == 1:
            price_ = f"numrange({Decimal(price[0])}, {Decimal(price[0])}, '[)')"
        else:
            price_ = f"numrange({Decimal(price[0])}, {Decimal(price[1])}, '[)')"

        try:
            query = f"""SELECT uuid_ptr_id FROM products_producttypes WHERE type LIKE '%{type}%'"""
            self.cursor.execute(query)
            type_id = self.cursor.fetchone()

            if type_id is None:
                type_uuid = uuid.uuid4()
                self.cursor.execute(f"""
                    INSERT INTO core_uuid (id, created_at, updated_at, is_active, is_deleted)
                    VALUES ('{type_uuid}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, true, false)
                """)
                query = f"""
                    INSERT INTO products_producttypes (uuid_ptr_id, type, valid_name)
                    VALUES ('{type_uuid}', '{type}', true) RETURNING uuid_ptr_id
                """
                self.cursor.execute(query)
                type_id = self.cursor.fetchone()[0]

            self.connection.commit()

        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Database error: {e}")

        try:
            self.cursor.execute(f"""
                INSERT INTO core_uuid(
                    id, created_at, updated_at, is_active, is_deleted
                ) VALUES('{uuid_ptr_id}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, true, false)
            """)
            self.cursor.execute(f"""
                INSERT INTO products_products VALUES (
                    '{uuid_ptr_id}',
                    '{name}',
                    '{description}',
                    '{brand}',
                    '{image}',
                    '{url}',
                    {items_sold},
                    {ratings},
                    '{condition}',
                    {original_price},
                    {price_},
                    {shipping_charges},
                    '{source}',
                    {discount},
                    '{type_id[0]}'
                );
            """)
            self.connection.commit()
            success = colorama.Fore.GREEN + f"""
                {item}
            """
            print(success)

        except psycopg2.IntegrityError:
            warning = colorama.Fore.YELLOW + f"""
                \nProduct Updated\n{item}\n\n\n
            """
            print(warning)
            query = f"""
                UPDATE products_products SET
                name='{name}',
                description='{description}',
                brand='{brand}',
                image='{image}',
                items_sold='{items_sold}',
                ratings='{ratings}',
                condition='{condition}',
                original_price='{original_price}',
                price='{price_}',
                shipping_charges='{shipping_charges}',
                source='{source}',
                discount='{discount}'
                type_id='{type_id}'
                WHERE url='{url}'
            """
            self.connection.commit()

        except Exception as e:
            error = colorama.Fore.RED + f"""
                \n{item}\n{e}\n\n\n
            """
            print(error)
            self.connection.rollback()

        return item
