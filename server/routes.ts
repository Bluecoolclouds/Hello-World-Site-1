import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import path from "path";
import Database from "better-sqlite3";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  app.get(api.greeting.get.path, async (req, res) => {
    const greeting = await storage.getGreeting();
    res.json(greeting || { message: "Привет, Мир" });
  });

  app.get("/api/bot-stats", async (req, res) => {
    try {
      const fs = await import("fs");
      const candidates = [
        path.resolve(process.cwd(), "bot.db"),
        path.resolve(process.cwd(), "bot/dating_bot.db"),
      ];
      const dbPath = candidates.find((p) => fs.existsSync(p));
      if (!dbPath) {
        return res.json({ totalUsers: 0, totalGirls: 0, totalMen: 0, activeChats: 0, onlineNow: 0 });
      }
      const db = new Database(dbPath, { readonly: true });

      const totalUsers = db.prepare("SELECT COUNT(*) as count FROM users").get() as any;
      const totalGirls = db.prepare("SELECT COUNT(*) as count FROM users WHERE is_girl = 1").get() as any;
      const totalMen = db.prepare("SELECT COUNT(*) as count FROM users WHERE is_girl = 0 OR is_girl IS NULL").get() as any;

      let activeChats = { count: 0 };
      try {
        activeChats = db.prepare("SELECT COUNT(*) as count FROM bot_chats WHERE is_active = 1").get() as any;
      } catch {}

      const onlineNow = db.prepare("SELECT COUNT(*) as count FROM users WHERE is_online = 1").get() as any;

      db.close();

      res.json({
        totalUsers: totalUsers?.count || 0,
        totalGirls: totalGirls?.count || 0,
        totalMen: totalMen?.count || 0,
        activeChats: activeChats?.count || 0,
        onlineNow: onlineNow?.count || 0,
      });
    } catch {
      res.json({
        totalUsers: 0,
        totalGirls: 0,
        totalMen: 0,
        activeChats: 0,
        onlineNow: 0,
      });
    }
  });

  return httpServer;
}
