import Foundation

/// Fixed by map seed and node ID; independent of the battle RNG cursor.
public enum CampaignSiteKind:String,Codable {case shop,satchel,spring}
public enum CampaignSiteRules {
    public static func kind(node:MapNode,seed:UInt64)->CampaignSiteKind? {
        if node.kind == .start{return .shop}
        guard node.kind == .empty else{return nil}
        var value=seed ^ (UInt64(truncatingIfNeeded:node.id) &* 0x9e3779b97f4a7c15) ^ 0x534954455331
        value=(value ^ (value >> 30)) &* 0xbf58476d1ce4e5b9
        value=(value ^ (value >> 27)) &* 0x94d049bb133111eb
        return [.shop,.satchel,.spring][Int((value ^ (value >> 31)) % 3)]
    }
}
extension Evaluation {
    func siteActor(_ id:String)throws->(GameUnit,Int,CampaignSiteKind) {
        let actor=try acting(id)
        guard state.phase == .exploration,state.battle==nil,actor.kind == .player,
              let index=state.map.nodes.firstIndex(where:{$0.id==actor.nodeID}),
              let kind=CampaignSiteRules.kind(node:state.map.nodes[index],seed:state.map.seed) else{throw GameError("当前地点没有商店或事件。")}
        return(actor,index,kind)
    }
    mutating func tradeCampaignSite(actor id:String,item itemID:String,buy:Bool)throws {
        var (actor,_,kind)=try siteActor(id)
        guard kind == .shop else{throw GameError("请到商店交易。")}
        let item=try catalog.item(itemID),price:Int
        if buy {
            guard let purchase=item.purchasePrice,purchase>0,item.setID==nil else{throw GameError("此物品不出售。")}
            price=purchase;guard actor.coins>=price else{throw GameError("购买者个人金币不足。")}
            actor.inventory[itemID]=try checkedAdd(actor.inventory[itemID] ?? 0,1);actor.coins-=price
        }else {
            price=item.sellPrice
            guard price>0,let count=actor.inventory[itemID],count>0 else{throw GameError("只能出售个人行囊内的物品，请先卸下已装备物品。")}
            actor.coins=try checkedAdd(actor.coins,price)
            if count==1{actor.inventory.removeValue(forKey:itemID)}else{actor.inventory[itemID]=count-1}
        }
        state.units[id]=actor
        events.append(GameEvent("campaignTrade",actor:id,amount:buy ? -price:price,detail:(buy ? "buy:":"sell:")+itemID))
    }
    mutating func resolveCampaignSite(actor id:String,accept:Bool)throws {
        var (actor,index,kind)=try siteActor(id)
        guard kind != .shop,state.map.nodes[index].siteResolved != true else{throw GameError("该事件已结束。")}
        var amount=0
        if accept {
            if kind == .satchel {amount=5;actor.coins=try checkedAdd(actor.coins,amount)}
            else {
                let maximum=try GameRules.attributes(actor,catalog:catalog).maximumHealth
                amount=min(4,max(0,maximum-actor.health))
                guard amount>0 else{throw GameError("当前成员生命已满，可换成员或离开此事件。")}
                actor.health+=amount
            }
        }
        state.units[id]=actor;state.map.nodes[index].siteResolved=true
        events.append(GameEvent("campaignSiteEvent",actor:id,amount:amount,detail:"\(actor.nodeID):\(kind.rawValue):\(accept ? "accept":"leave")"))
    }
}
