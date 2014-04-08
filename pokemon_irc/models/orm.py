#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String,\
    ForeignKey, Float, Date, Numeric, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from settings import DATABASE_URI

Base = declarative_base()
engine = create_engine(DATABASE_URI)


class PokemonType(Base):
    __tablename__ = "pokemon_type"
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey('pokemon.id')),
    type_id = Column(Integer, ForeignKey('type.id'))


class DefaultColumns:
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)


class Pokemon(Base, DefaultColumns):
    __tablename__ = 'pokemon'
    # type = Column(Integer, ForeignKey("type.id"))
    types = relationship("Type", secondary="pokemon_type")
    hp = Column(Integer)
    attack = Column(Integer)
    defence = Column(Integer)
    special_attack = Column(Integer)
    special_defence = Column(Integer)
    speed = Column(Integer)


class Type(Base, DefaultColumns):
    __tablename__ = 'type'


class DamageTypesRelation(Base):
    __tablename__ = 'damage_types_relation'
    id = Column(Integer, primary_key=True)
    attack = Column(Integer, ForeignKey("type.id"))
    defence = Column(Integer, ForeignKey("type.id"))
    # attack = relationship('Type')
    # defence = relationship('Type')
    dmg = Column(Float)


class MoveCategory(Base, DefaultColumns):
    __tablename__ = 'move_category'


class Move(Base, DefaultColumns):
    __tablename__ = 'move'
    type = Column(Integer, ForeignKey("type.id"))
    category = Column(Integer, ForeignKey("move_category.id"))
    power = Column(Integer)
    accuracy = Column(Integer)
    pp = Column(Integer)
    effect = Column(Integer, ForeignKey("effect.id"))


class Ability(Base, DefaultColumns):
    __tablename__ = 'ability'


class Effect(Base, DefaultColumns):
    __tablename__ = 'effect'
    description = Column(String(150), unique=True)

Base.metadata.create_all(engine)
