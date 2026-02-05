import { db } from "./db";
import {
  greetings,
  type InsertGreeting,
  type Greeting
} from "@shared/schema";

export interface IStorage {
  getGreeting(): Promise<Greeting | undefined>;
}

export class DatabaseStorage implements IStorage {
  async getGreeting(): Promise<Greeting | undefined> {
    // Return a static greeting or fetch from DB if we seeded it
    return { id: 1, message: "Привет, Мир" };
  }
}

export const storage = new DatabaseStorage();
