package org.talor.wurmunlimited.mods.permadeath;

import com.wurmonline.server.Players;
import com.wurmonline.server.players.Player;
import org.gotti.wurmunlimited.modloader.classhooks.HookManager;
import org.gotti.wurmunlimited.modloader.classhooks.InvocationHandlerFactory;
import org.gotti.wurmunlimited.modloader.interfaces.*;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.util.Properties;


public class Permadeath implements WurmServerMod, Configurable, ServerStartedListener, Initable, PreInitable {


    // Configuration default values
    private boolean permadeath = true;

    @Override
	public void onServerStarted() {
	}

	@Override
	public void configure(Properties properties) {
        // Check .properties file for configuration values
        permadeath = Boolean.parseBoolean(properties.getProperty("permadeath", Boolean.toString(permadeath)));
	}

	@Override
	public void preInit() {
	}

	@Override
	public void init() {

        HookManager.getInstance().registerHook("com.wurmonline.server.players.Player", "setDeathEffects", "(ZII)V", new InvocationHandlerFactory() {

            @Override
            public InvocationHandler createInvocationHandler() {
                return new InvocationHandler() {

                    @Override
                    public Object invoke(Object object, Method method, Object[] args) throws Throwable {

                        Player player = (Player) object;

                        if (permadeath && player.getPower() < 2) {
                            player.ban("You are banned because you are dead", 9223372036854775807L);
                            Players.getInstance().removeBannedIp(player.getCommunicator().getConnection().getIp());
                            return method.invoke(object, args);
                        } else {
                            return method.invoke(object, args);
                        }
                    }
                };
            }
        });

    }
}

