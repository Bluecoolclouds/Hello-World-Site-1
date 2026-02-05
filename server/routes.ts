import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  app.get(api.greeting.get.path, async (req, res) => {
    const greeting = await storage.getGreeting();
    res.json(greeting || { message: "Привет, Мир" });
  });

  return httpServer;
}
